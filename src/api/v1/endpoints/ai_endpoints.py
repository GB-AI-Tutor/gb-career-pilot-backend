import json
import logging
import re
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from src.api.v1.deps import get_current_user
from src.database.database import get_supabase_admin_client
from src.schemas.ai_schemas import ChatRequest
from src.services.ai_tools import tools
from src.services.brave_search_service import brave_search
from src.services.coversation_history import (
    convertion_history,
    extract_and_update_memory,
    get_counselor_prompt,
)
from src.services.university_service import get_universities_from_db
from src.utils.ai_client import client, get_basic_completion

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test-api")
def test_groq_connection(prompt: str):
    answer = get_basic_completion(prompt)
    return {"AI_reponse": answer}


@router.post("/chat")
def chat(
    chatlist: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    # rate_limit_check: bool = Depends(rate_limiter) # Uncomment when you add Issue #31
):
    db = get_supabase_admin_client()

    # 1. ID Validation & Message Extraction
    conv_id = chatlist.conversation_id if chatlist.conversation_id else None
    user_messages = [m.model_dump(mode="json") for m in chatlist.messages]
    last_msg = user_messages[-1]["content"]

    current_memory = {}

    # 2. Conversation & Memory Setup
    if not conv_id:
        title = (last_msg[:25] + "...") if len(last_msg) > 25 else last_msg
        new_conv = (
            db.table("conversations")
            .insert({"user_id": current_user["id"], "title": title})
            .execute()
        )
        conv_id = new_conv.data[0]["id"]
    else:
        conv_data = db.table("conversations").select("memory").eq("id", conv_id).execute()
        if conv_data.data:
            current_memory = conv_data.data[0].get("memory", {})

    # 3. Dynamic Prompt Injection (Using your new templates!)
    memory_string = json.dumps(current_memory, indent=2)
    system_prompt = get_counselor_prompt(memory_string)

    # 4. Save User Message
    db.table("messages").insert(
        {"conversation_id": conv_id, "role": "user", "content": last_msg}
    ).execute()

    # 5. Assemble History
    previous_conversations = []
    if conv_id:
        previous_conversations = convertion_history(conv_id)

    final_history = [system_prompt] + previous_conversations

    # 6. First LLM Call: Decision Phase (Non-streaming to catch tools)
    response = client.chat.completions.create(
        messages=final_history,
        model="llama-3.1-8b-instant",
        tools=tools,
        tool_choice="auto",
        stream=False,
    )
    message = response.choices[0].message
    content_text = message.content or ""

    # --- 🛡️ THE HALLUCINATION INTERCEPTOR ---
    if not message.tool_calls and "function=" in content_text:
        pattern = r"<.*?function=([^>]+)>(.*?)</function>"
        matches = re.findall(pattern, content_text)

        if matches:

            class MockFunction:
                def __init__(self, name, arguments):
                    self.name, self.arguments = name, arguments

            class MockToolCall:
                def __init__(self, id, function):
                    self.id, self.function = id, function

                def model_dump(self):
                    return {
                        "id": self.id,
                        "type": "function",
                        "function": {
                            "name": self.function.name,
                            "arguments": self.function.arguments,
                        },
                    }

            mock_tool_calls = [
                MockToolCall(
                    id=f"call_{uuid.uuid4().hex[:4]}", function=MockFunction(name=n, arguments=a)
                )
                for n, a in matches
            ]
            message.tool_calls = mock_tool_calls
            message.content = None
    # ----------------------------------------

    # --- 💾 HELPER: Save Final State ---
    # We use this helper inside our generators so we don't repeat code
    def save_final_state(final_text: str):
        db.table("messages").insert(
            {"role": "assistant", "conversation_id": conv_id, "content": final_text}
        ).execute()

        recent_context = final_history[-4:] + [{"role": "assistant", "content": final_text}]
        try:
            # We call this directly instead of using background_tasks because
            # StreamingResponse behaves differently with background tasks.
            extract_and_update_memory(conv_id, recent_context, current_memory, db)
        except Exception as e:
            print(f"Memory update failed: {e}")

    # -----------------------------------

    # 7. Handle Tool Calls & Streaming
    if message.tool_calls:
        # Save Assistant's Request
        db.table("messages").insert(
            {
                "conversation_id": conv_id,
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [t.model_dump() for t in message.tool_calls],
            }
        ).execute()

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            tool_name = tool_call.function.name

            if tool_name == "search_universities":
                tool_result = get_universities_from_db(**args)
            elif tool_name == "brave_search":
                tool_result = brave_search(args.get("query", ""), args.get("count", 5))
            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}

            # Save Tool's Result & Update History
            db.table("messages").insert(
                {
                    "conversation_id": conv_id,
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result),
                }
            ).execute()

            final_history.extend(
                [
                    message,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result),
                    },
                ]
            )

        # 🌊 GENERATOR A: Tool-Assisted Stream
        def generate_tool_stream():
            final_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=final_history,
                stream=True,  # Turn on streaming!
            )
            full_text = ""
            for chunk in final_response:
                if chunk.choices[0].delta.content is not None:
                    text_chunk = chunk.choices[0].delta.content
                    full_text += text_chunk
                    yield f"data: {text_chunk}\n\n"

            save_final_state(full_text)
            yield f"data: [DONE_CONV_ID:{conv_id}]\n\n"

        return StreamingResponse(generate_tool_stream(), media_type="text/event-stream")

    else:
        # 🌊 GENERATOR B: Instant Stream (No tools used)
        def generate_instant_stream():
            full_text = message.content or ""
            # Yield the whole text at once, but in the SSE format the frontend expects
            yield f"data: {full_text}\n\n"

            save_final_state(full_text)
            yield f"data: [DONE_CONV_ID:{conv_id}]\n\n"

        return StreamingResponse(generate_instant_stream(), media_type="text/event-stream")
