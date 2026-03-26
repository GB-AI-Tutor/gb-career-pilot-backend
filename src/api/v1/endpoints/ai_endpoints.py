import json
import logging
import re
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from src.api.v1.deps import get_current_user, rate_limiter
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


def sse_data_event(payload: str) -> str:
    """Format payload as a valid SSE data event (supports multiline text)."""
    text = "" if payload is None else str(payload)
    lines = text.splitlines() or [""]
    return "".join(f"data: {line}\n" for line in lines) + "\n"


# --- 🔄 HELPER: Serialize Messages for Groq API ---
def serialize_messages_for_groq(messages: list) -> list:
    """
    Convert messages to plain dicts for Groq API, whitelisting only expected fields.
    Removes any Pydantic internals, annotations, or unsupported properties.
    Ensures all tool_calls have required 'type' field.
    Validates that all messages have required 'role' field.
    """
    serialized = []
    for i, msg in enumerate(messages):
        # Convert to dict if it's a Pydantic model
        if hasattr(msg, "model_dump"):
            msg_dict = msg.model_dump()
        elif isinstance(msg, dict):
            msg_dict = msg.copy()
        else:
            msg_dict = msg

        # Whitelist only fields that Groq API expects
        # This strips out Pydantic internals, annotations, and any other unsupported properties
        cleaned_msg = {}

        if isinstance(msg_dict, dict):
            # ✅ CRITICAL: Validate required 'role' field
            if not msg_dict.get("role") or msg_dict["role"] is None:
                logger.error(
                    f"❌ Message at index {i} missing/null 'role' field. Skipping to prevent API error."
                )
                continue

            # Always include role and content
            if "role" in msg_dict:
                cleaned_msg["role"] = msg_dict["role"]
            if "content" in msg_dict:
                cleaned_msg["content"] = msg_dict["content"]

            # Include tool_calls if present (for assistant messages)
            if "tool_calls" in msg_dict and msg_dict["tool_calls"]:
                tool_calls = []
                for tc in msg_dict["tool_calls"]:
                    # Ensure each tool_call has required 'type' field
                    if isinstance(tc, dict):
                        tc_copy = tc.copy()
                        if "type" not in tc_copy:
                            tc_copy["type"] = "function"
                        tool_calls.append(tc_copy)
                cleaned_msg["tool_calls"] = tool_calls

            # Include tool_call_id if present (for tool messages)
            if "tool_call_id" in msg_dict:
                cleaned_msg["tool_call_id"] = msg_dict["tool_call_id"]

        serialized.append(cleaned_msg)

    logger.info(f"✅ Serialized {len(serialized)} valid messages for Groq API")
    return serialized


# ---


@router.post("/test-api")
def test_groq_connection(prompt: str):
    answer = get_basic_completion(prompt)
    return {"AI_reponse": answer}


@router.post("/chat")
def chat(
    chatlist: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    rate_limit_check: bool = Depends(rate_limiter),
):
    """
    AI Chat Endpoint

    Stream AI responses for university guidance using Groq LLM.

    **Rate Limit:** 20 requests per hour per authenticated user (tracked in database)

    **Features:**
    - Tool calling (university search, web search)
    - Conversation history and memory
    - Server-Sent Events (SSE) streaming
    - Hallucination detection and correction

    **Authentication:** Required (Bearer token)

    **Returns:** StreamingResponse with SSE format
    """
    # raise Exception("This is a fake crash to test my global handler!")
    db = get_supabase_admin_client()

    # 1. ID Validation & Message Extraction
    conv_id = str(chatlist.conversation_id) if chatlist.conversation_id else None
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
    memory_string = json.dumps(current_memory, indent=2, default=str)
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
        messages=serialize_messages_for_groq(final_history),  # ← Serialize for Groq
        model="llama-3.1-8b-instant",
        tools=tools,
        tool_choice="auto",
        stream=False,
        max_tokens=2048,  # Prevent truncation - Groq default might be low
    )
    message = response.choices[0].message
    content_text = message.content or ""

    logger.info(
        f"📨 First LLM Response - Tool Calls: {bool(message.tool_calls)}, Content Length: {len(content_text)}, Content: {content_text[:100]}"
    )

    # --- 🛡️ THE HALLUCINATION INTERCEPTOR (IMPROVED) ---
    if not message.tool_calls and content_text and "<function" in content_text.lower():
        # Support both formats:
        # 1) <function=search_universities>{...}</function>
        # 2) <function/search_universities>{...}</function>
        equals_pattern = r"<\s*function\s*=\s*([^>]+)>(.*?)</\s*function\s*>"
        slash_pattern = r"<\s*function\s*/\s*([^>\s]+)\s*>(.*?)</\s*function\s*>"

        matches = re.findall(equals_pattern, content_text, re.DOTALL)
        matches.extend(re.findall(slash_pattern, content_text, re.DOTALL))

        if matches:
            logger.info(f"🚨 Hallucination detected: {len(matches)} function call(s)")

            mock_tool_calls = []
            for raw_name, raw_args in matches:
                name = raw_name.strip().strip("\"'")
                args = (raw_args or "").strip()
                if not args:
                    args = "{}"
                mock_tool_calls.append(
                    {
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": args,
                        },
                    }
                )

            # Strip ALL function call patterns from content to prevent leaking to frontend
            cleaned_content = re.sub(equals_pattern, "", content_text, flags=re.DOTALL)
            cleaned_content = re.sub(slash_pattern, "", cleaned_content, flags=re.DOTALL).strip()

            message.tool_calls = mock_tool_calls
            message.content = cleaned_content if cleaned_content else None
            logger.info(f"✅ Converted to {len(mock_tool_calls)} tool call(s). Content cleaned.")
        else:
            # Regex didn't match but function tags are present - attempt fallback cleaning
            if "<" in content_text and ">" in content_text:
                logger.warning("⚠️ Possible function call not caught by primary regex pattern")
                # Clean content by removing anything that looks like XML tags with 'function'
                cleaned = re.sub(
                    r"<[^>]*function[^>]*>.*?</[^>]*>", "", content_text, flags=re.DOTALL
                )
                if cleaned != content_text:
                    message.content = cleaned.strip() or None
                    logger.info("✅ Cleaned suspicious XML patterns from content")
    # ----------------------------------------

    # --- 💾 HELPER: Save Final State ---
    # We use this helper inside our generators so we don't repeat code
    def save_final_state(final_text: str):
        db.table("messages").insert(
            {"role": "assistant", "conversation_id": conv_id, "content": final_text}
        ).execute()

        # ⚠️ CRITICAL: Sanitize messages before memory extraction
        # Messages in final_history may contain tool_calls without 'type' field
        recent_context = serialize_messages_for_groq(
            final_history[-4:] + [{"role": "assistant", "content": final_text}]
        )
        try:
            # We call this directly instead of using background_tasks because
            # StreamingResponse behaves differently with background tasks.
            extract_and_update_memory(conv_id, recent_context, current_memory, db)
        except Exception as e:
            print(f"Memory update failed: {e}")

    # -----------------------------------

    # 7. Handle Tool Calls & Streaming
    if message.tool_calls:
        # Normalize tool_calls to dict format to handle SDK objects and mocked dicts consistently
        tool_calls_for_db = []
        for t in message.tool_calls:
            if hasattr(t, "model_dump"):
                tc = t.model_dump()
            elif isinstance(t, dict):
                tc = t.copy()
            else:
                tc = {
                    "id": getattr(t, "id", f"call_{uuid.uuid4().hex[:8]}"),
                    "function": {
                        "name": getattr(getattr(t, "function", None), "name", ""),
                        "arguments": getattr(getattr(t, "function", None), "arguments", "{}"),
                    },
                }

            if "type" not in tc:
                tc["type"] = "function"
            if "id" not in tc:
                tc["id"] = f"call_{uuid.uuid4().hex[:8]}"
            if "function" not in tc or not isinstance(tc["function"], dict):
                tc["function"] = {"name": "", "arguments": "{}"}
            tc["function"].setdefault("name", "")
            tc["function"].setdefault("arguments", "{}")

            tool_calls_for_db.append(tc)

        # Save Assistant's Request with validated tool_calls
        db.table("messages").insert(
            {
                "conversation_id": conv_id,
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": tool_calls_for_db,
            }
        ).execute()

        for tool_call in tool_calls_for_db:
            raw_args = tool_call["function"].get("arguments") or "{}"
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                logger.warning(
                    f"⚠️ Invalid tool arguments JSON, defaulting to empty object: {raw_args}"
                )
                args = {}

            tool_name = tool_call["function"].get("name", "")

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
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, default=str),
                }
            ).execute()

            # Convert message object to proper dict format before adding to history
            assistant_message_dict = {
                "role": "assistant",
                "content": message.content or "",
            }
            if tool_calls_for_db:
                # Ensure tool_calls have proper format with 'type' field
                assistant_message_dict["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                    for tc in tool_calls_for_db
                ]

            final_history.extend(
                [
                    assistant_message_dict,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result, default=str),
                    },
                ]
            )

        # 🌊 GENERATOR A: Tool-Assisted Stream
        def generate_tool_stream():
            try:
                final_response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=serialize_messages_for_groq(final_history),  # ← Serialize for Groq
                    stream=True,  # Turn on streaming!
                    max_tokens=2048,  # Prevent truncation
                )
                full_text = ""
                for chunk in final_response:
                    if chunk.choices[0].delta.content is not None:
                        text_chunk = chunk.choices[0].delta.content
                        full_text += text_chunk
                        yield sse_data_event(text_chunk)

                try:
                    save_final_state(full_text)
                except Exception as e:
                    logger.error(f"❌ Error saving final state in tool stream: {e}", exc_info=True)
                    yield sse_data_event("[ERROR: Failed to save response]")

                yield sse_data_event(f"[DONE_CONV_ID:{conv_id}]")
            except Exception as e:
                logger.error(f"❌ Error in tool stream generation: {e}", exc_info=True)
                yield sse_data_event(f"[ERROR: {str(e)}]")

        return StreamingResponse(generate_tool_stream(), media_type="text/event-stream")

    else:
        # 🌊 GENERATOR B: Instant Stream (No tools used)
        def generate_instant_stream():
            try:
                full_text = message.content or ""
                logger.info(
                    f"🎯 Instant stream - No tools triggered. Returning {len(full_text)} chars"
                )
                # Yield the whole text at once, but in the SSE format the frontend expects
                yield sse_data_event(full_text)

                try:
                    save_final_state(full_text)
                except Exception as e:
                    logger.error(
                        f"❌ Error saving final state in instant stream: {e}", exc_info=True
                    )
                    yield sse_data_event("[ERROR: Failed to save response]")

                yield sse_data_event(f"[DONE_CONV_ID:{conv_id}]")
            except Exception as e:
                logger.error(f"❌ Error in instant stream generation: {e}", exc_info=True)
                yield sse_data_event(f"[ERROR: {str(e)}]")

        return StreamingResponse(generate_instant_stream(), media_type="text/event-stream")
