import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends

from src.api.v1.deps import get_current_user
from src.database.database import get_supabase_admin_client
from src.schemas.ai_schemas import ChatRequest
from src.services.ai_tools import tools
from src.services.brave_search_service import brave_search
from src.services.coversation_history import convertion_history, extract_and_update_memory
from src.services.university_service import get_universities_from_db
from src.utils.ai_client import client, get_basic_completion

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test-api")
def test_groq_connection(prompt: str):
    answer = get_basic_completion(prompt)
    return {"AI_reponse": answer}


# @router.post("/chat")
# def chat(chatlist: ChatRequest,background_tasks: BackgroundTasks, current_user : dict=Depends(get_current_user)):
#     # ... (System prompt and history setup)
# #  ... (Your system_prompt and final_history logic remains the same)
#     system_prompt = {
#         "role": "system",
#         "content": "You are a helpful AI Tutor for students in Gilgit Baltistan. You have access to two tools: 1) search_universities - a local database of Pakistani universities (primary source), 2) brave_search - web search as a fallback. Always try search_universities first for university-related queries. Use brave_search only when you need additional context or when information is not available in the local database."
#     }
#     db=get_supabase_admin_client()
#     conv_id = chatlist.conversation_id if chatlist.conversation_id else None

#     user_messages = [m.model_dump(mode="json") for m in chatlist.messages]
#     last_msg = user_messages[-1]['content']

#     current_memory={}
#     if not conv_id:
#         # Generate title and create new conversation
#         title = (last_msg[:25] + '...') if len(last_msg) > 25 else last_msg
#         new_conv = db.table("conversations").insert({
#             "user_id": current_user['id'],
#             "title": title
#         }).execute()
#         conv_id = new_conv.data[0]["id"]
#     else:
#         #fetching existing memory fo this specific convercation
#         conv_data = db.table("convesations").select("memory").eq("id",conv_id).execute()
#         if conv_data.data:
#             current_memory = conv_data.data[0].get("memory",{})

#     # 1. Convert the Python dictionary into a cleanly formatted string
#     memory_string   = json.dumps(current_memory, indent=2)

#     # 2. Inject it with clear boundaries
#     system_prompt = {
#         "role": "system",
#         "content": (
#             "You are a helpful AI Tutor for students in Gilgit Baltistan. "
#             "You have access to two tools: 1) search_universities, 2) brave_search. "
#             "Always try search_universities first. \n\n"
#             "--- STUDENT CONTEXT (MEMORY) ---\n"
#             "Use these facts to personalize your advice and university recommendations. "
#             "Do not ask the student for this information if it is already provided below:\n"
#             f"{memory_string}\n"
#             "--------------------------------\n"
#         )
#     }

# # Capture the newly created UUID
#     db.table("messages").insert({
#         "conversation_id": conv_id,
#         "role": user_messages[0]['role'],
#         "content": user_messages[0]['content']
#     }).execute()

#     # Only fetch if we have an ID
#     previous_conversations = []
#     if conv_id:
#         previous_conversations = convertion_history(conv_id)

#     #we didn't add the user message because we already added it to database which come in previous_conversations
#     final_history = [system_prompt] + previous_conversations

#     # 1. First call: Non-streaming to get the decision quickly ⚡
#     response = client.chat.completions.create(
#         messages=final_history,
#         model="llama-3.1-8b-instant",
#         tools=tools,
#         tool_choice="auto",
#         stream=False # 👈 Fast, structured response
#     )

#     message = response.choices[0].message

#     # Debug: Log what we're getting from the model
#     logger.info(f"Model response - tool_calls: {message.tool_calls}, content: {message.content}")

#     ai_response_text=""
#     # 2. Handle Tool Calls
#     if message.tool_calls:
#     # STEP A: Save the Assistant's "Request" message first
#     # This message tells the history that the AI DECIDED to use tools
#         db.table("messages").insert({
#             "conversation_id": conv_id,
#             "role": "assistant",
#             "content": message.content or "", # Content is often null when tool_calls exist
#             "tool_calls": [t.model_dump() for t in message.tool_calls] # Serialize the calls
#         }).execute()

#         for tool_call in message.tool_calls:
#             args = json.loads(tool_call.function.arguments)
#             tool_name = tool_call.function.name

#             if tool_name == "search_universities":
#                 tool_result = get_universities_from_db(**args)
#             elif tool_name == "brave_search":
#                 tool_result = brave_search(args.get("query", ""), args.get("count", 5))
#             else:
#                 tool_result = {"error": f"Unknown tool: {tool_name}"}

#             # STEP B: Save the Tool's "Result" message
#             # This links the specific result to the request using tool_call_id
#             db.table("messages").insert({
#                 "conversation_id": conv_id,
#                 "role": "tool",
#                 "tool_call_id": tool_call.id,
#                 "content": json.dumps(tool_result) # The actual search data
#             }).execute()

#             # Update local history for the very next AI call
#             final_history.append(message)
#             final_history.append({
#                 "role": "tool",
#                 "tool_call_id": tool_call.id,
#                 "content": json.dumps(tool_result)
#             })
#         # 3. Final call: Generate the human-friendly answer
#         final_response = client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=final_history,
#             stream=False # Keep it non-streaming for the fastest total response time
#         )
#         ai_response_text=final_response.choices[0].message.content

#     else:
#         ai_response_text = message.content

#     db.table("messages").insert({"role":"assistant","conversation_id":conv_id,"content":ai_response_text}).execute()
#     # --- NEW: TRIGGER BACKGROUND MEMORY EXTRACTION ---
#     # Grab the last few messages to give the extractor context (e.g., the last 4)
#     recent_context = final_history[-4:] + [{"role": "assistant", "content": ai_response_text}]

#     background_tasks.add_task(
#         extract_and_update_memory,
#         conv_id=conv_id,
#         recent_messages=recent_context,
#         current_memory=current_memory,
#         db_client=db
#     )
#     return {"content": ai_response_text}


@router.post("/chat")
def chat(
    chatlist: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    db = get_supabase_admin_client()

    # 1. ID Validation & Message Extraction
    conv_id = chatlist.conversation_id if chatlist.conversation_id else None
    user_messages = [m.model_dump(mode="json") for m in chatlist.messages]
    last_msg = user_messages[-1]["content"]  # The most recent thing the student typed

    current_memory = {}

    # 2. Conversation & Memory Setup
    if not conv_id:
        # Generate title and create new conversation
        title = (last_msg[:25] + "...") if len(last_msg) > 25 else last_msg
        new_conv = (
            db.table("conversations")
            .insert({"user_id": current_user["id"], "title": title})
            .execute()
        )
        conv_id = new_conv.data[0]["id"]
    else:
        # Fetch existing memory for this specific conversation (Typo fixed here!)
        conv_data = db.table("conversations").select("memory").eq("id", conv_id).execute()
        if conv_data.data:
            current_memory = conv_data.data[0].get("memory", {})

    # 3. Dynamic Prompt Injection
    memory_string = json.dumps(current_memory, indent=2)
    system_prompt = {
        "role": "system",
        "content": (
            "You are a helpful AI Tutor for students in Gilgit Baltistan. "
            "You have access to two tools: 1) search_universities, 2) brave_search. "
            "Always try search_universities first. \n\n"
            "--- STUDENT CONTEXT (MEMORY) ---\n"
            "Use these facts to personalize your advice and university recommendations. "
            "Do not ask the student for this information if it is already provided below:\n"
            f"{memory_string}\n"
            "--------------------------------\n"
        ),
    }

    # 4. Save User Message (Using the safer last_msg variable)
    db.table("messages").insert(
        {"conversation_id": conv_id, "role": "user", "content": last_msg}
    ).execute()

    # 5. Assemble History
    previous_conversations = []
    if conv_id:
        previous_conversations = convertion_history(conv_id)  # Fetches last 15, Oldest -> Newest

    final_history = [system_prompt] + previous_conversations

    # 6. First LLM Call: Decision Phase
    response = client.chat.completions.create(
        messages=final_history,
        model="llama-3.1-8b-instant",
        tools=tools,
        tool_choice="auto",
        stream=False,
    )
    message = response.choices[0].message
    ai_response_text = ""

    # 7. Handle Tool Calls
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

            # Save Tool's Result
            db.table("messages").insert(
                {
                    "conversation_id": conv_id,
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result),
                }
            ).execute()

            # Append to temporary history
            final_history.append(message)
            final_history.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(tool_result)}
            )

        # Final LLM Call for the human-friendly answer
        final_response = client.chat.completions.create(
            model="llama-3.1-8b-instant", messages=final_history, stream=False
        )
        ai_response_text = final_response.choices[0].message.content

    else:
        ai_response_text = message.content

    # 8. Save Final Answer
    db.table("messages").insert(
        {"role": "assistant", "conversation_id": conv_id, "content": ai_response_text}
    ).execute()

    # 9. Trigger Background Memory Extraction
    recent_context = final_history[-4:] + [{"role": "assistant", "content": ai_response_text}]
    background_tasks.add_task(
        extract_and_update_memory,
        conv_id=conv_id,
        recent_messages=recent_context,
        current_memory=current_memory,
        db_client=db,
    )

    # 10. Return Answer AND the ID to the frontend
    return {"content": ai_response_text, "conversation_id": conv_id}
