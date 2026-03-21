import json
from uuid import UUID

from src.database.database import get_supabase_admin_client
from src.utils.ai_client import client

db = get_supabase_admin_client()


def convertion_history(conversation_id: UUID, limit_count: int = 15):
    # Pagination is also added to get most recent message not all mesasge history
    response = (
        db.table("messages")
        .select("role", "content", "tool_calls", "tool_call_id")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(limit_count)
        .execute()
    )
    history = response.data
    history.reverse()

    # Clean up messages to ensure tool_calls is only present for assistant messages
    cleaned_history = []
    for msg in history:
        cleaned_msg = {"role": msg["role"], "content": msg["content"]}

        # Only include tool_calls for assistant messages
        if msg["role"] == "assistant" and msg.get("tool_calls"):
            cleaned_msg["tool_calls"] = msg["tool_calls"]

        # Only include tool_call_id for tool messages
        if msg["role"] == "tool" and msg.get("tool_call_id"):
            cleaned_msg["tool_call_id"] = msg["tool_call_id"]

        cleaned_history.append(cleaned_msg)

    return cleaned_history


def extract_and_update_memory(
    conv_id: UUID, recent_messages: list, current_memory: dict, db_client
):
    # 1. The Strict Extraction Prompt
    extractor_prompt = {
        "role": "system",
        "content": (
            "You are a background data extraction assistant. "
            "Your job is to read the recent conversation and extract facts into a strict JSON object. "
            "Track these keys: 'current_education', 'academic_goals' (use a list with the current goal at index 0), "
            "'financial_constraints', and 'location_preferences'.\n\n"
            "RULES:\n"
            "1. Output ONLY valid JSON. No markdown, no explanations.\n"
            "2. If a value is unknown, omit the key or use null.\n"
            "3. If the student states a NEW preference, OVERWRITE the old one.\n"
            f"CURRENT MEMORY STATE: {json.dumps(current_memory)}"
        ),
    }

    # 2. Add the recent chat context (e.g., the last 3-4 messages)
    extraction_history = [extractor_prompt] + recent_messages

    # 3. Call the AI (Notice we force JSON output!)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Or whichever Groq model you prefer
        messages=extraction_history,
        response_format={"type": "json_object"},  # 👈 Crucial for data extraction
        temperature=0.1,  # Keep it low so the AI doesn't get "creative" with facts
    )

    try:
        # 4. Parse the AI's output
        new_memory_json = json.loads(response.choices[0].message.content)

        # 5. Save the updated memory back to Supabase
        db_client.table("conversations").update({"memory": new_memory_json}).eq(
            "id", conv_id
        ).execute()

    except Exception as e:
        print(f"Failed to update memory: {e}")


# prompts.py


def get_counselor_prompt(memory_string: str = "{}") -> dict:
    return {
        "role": "system",
        "content": (
            "You are a helpful AI Tutor for students in Gilgit Baltistan. "
            "You have access to two tools: 1) search_universities, 2) brave_search. "
            "Always try search_universities first. \n\n"
            "--- STUDENT CONTEXT (MEMORY) ---\n"
            "Use these facts to personalize your advice and university recommendations. "
            "Do not ask the student for this information if it is already provided below:\n"
            "Do NOT output raw <function> tags in your text. Always use the standard JSON tool-calling structure\n"
            "Never use phrases like 'Based on the search results' or 'Here is what I found'. Speak directly and naturally as a mentor."
            "When asked about the 'best' universities, prioritize nationally recognized top-tier institutions for that specific field first, then apply regional context or quotas."
            "Always mention specific entry tests (e.g., NET, NTS NAT, ECAT) when discussing admissions in Pakistan."
            f"{memory_string}\n"
            "--------------------------------\n"
        ),
    }


def get_extractor_prompt(current_memory_json: str) -> dict:
    return {
        "role": "system",
        "content": (
            "You are a background data extraction assistant. "
            "Your job is to read the recent conversation and extract facts into a strict JSON object. "
            "Track these keys: 'current_education', 'academic_goals' (use a list with the current goal at index 0), "
            "'financial_constraints', and 'location_preferences'.\n\n"
            "RULES:\n"
            "1. Output ONLY valid JSON. No markdown.\n"
            "2. If a value is unknown, omit the key or use null.\n"
            "3. If the student states a NEW preference, OVERWRITE the old one.\n"
            f"CURRENT MEMORY STATE: {current_memory_json}"
        ),
    }
