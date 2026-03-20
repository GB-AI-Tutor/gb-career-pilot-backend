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
    return history


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
