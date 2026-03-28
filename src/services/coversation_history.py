import json
import logging
from typing import Any, cast
from uuid import UUID

from src.database.database import get_supabase_admin_client
from src.utils.ai_client import client

db = get_supabase_admin_client()
logger = logging.getLogger(__name__)


def convertion_history(conversation_id: UUID | str, limit_count: int = 15):
    conversation_id = str(conversation_id)
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
        # CRITICAL: Validate required fields exist and are not None
        if not msg.get("role") or msg["role"] is None:
            logger.warning(f" Skipping message with missing/null role field: {msg}")
            continue

        if not msg.get("content") and msg.get("role") != "tool":
            # For non-tool messages, content should exist
            logger.warning(f" Skipping message with null content: role={msg['role']}")
            continue

        cleaned_msg = {"role": msg["role"], "content": msg["content"]}

        # Only include tool_calls for assistant messages and ensure 'type' field exists
        if msg["role"] == "assistant" and msg.get("tool_calls"):
            tool_calls = msg["tool_calls"]

            # Validate and ensure each tool_call has required 'type' field
            validated_tool_calls = []
            for tc in tool_calls:
                if isinstance(tc, dict):
                    # Add 'type' field if missing (Groq API requirement)
                    if "type" not in tc:
                        tc["type"] = "function"
                    validated_tool_calls.append(tc)

            if validated_tool_calls:
                cleaned_msg["tool_calls"] = validated_tool_calls

        # Only include tool_call_id for tool messages
        if msg["role"] == "tool" and msg.get("tool_call_id"):
            cleaned_msg["tool_call_id"] = msg["tool_call_id"]

        cleaned_history.append(cleaned_msg)

    return cleaned_history


def extract_and_update_memory(
    conv_id: UUID | str, recent_messages: list, current_memory: dict, db_client
):
    conv_id = str(conv_id)
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
            f"CURRENT MEMORY STATE: {json.dumps(current_memory, default=str)}"
        ),
    }

    # 2. Keep memory extraction context compact to avoid TPM limits
    compact_recent_messages: list[dict[str, Any]] = []
    for msg in recent_messages[-2:]:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if not role:
            continue
        if role not in {"user", "assistant"}:
            # Tool messages require tool_call_id for chat API format.
            # They are not needed for memory extraction, so skip them.
            continue
        compact_recent_messages.append(
            {
                "role": role,
                "content": str(content)[:500] if content is not None else "",
            }
        )

    extraction_history: list[dict[str, Any]] = [extractor_prompt] + compact_recent_messages

    # 3. DEFENSIVE: Ensure tool_calls have required 'type' field (Groq API requirement)
    # This protects against corrupted messages from database or earlier processing
    for msg in extraction_history:
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict) and "type" not in tc:
                    tc["type"] = "function"
                    logger.warning(" Added missing 'type' field to tool_call in extraction_history")

    # 4. Call the AI (Notice we force JSON output!)
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=cast(Any, extraction_history),
            response_format={"type": "json_object"},  # Crucial for data extraction
            temperature=0.1,  # Keep it low so the AI doesn't get "creative" with facts
            max_tokens=300,
        )
    except Exception as e:
        error_text = str(e)
        if "rate_limit_exceeded" in error_text or "tokens" in error_text:
            logger.warning(
                " Skipping memory update due to Groq TPM limit; chat response already delivered."
            )
            return
        raise

    try:
        # 4. Parse the AI's output
        memory_payload = response.choices[0].message.content or "{}"
        new_memory_json = json.loads(memory_payload)

        # 5. Save the updated memory back to Supabase
        db_client.table("conversations").update({"memory": new_memory_json}).eq(
            "id", conv_id
        ).execute()

    except Exception as e:
        logger.warning(f"Failed to update memory: {e}")


def get_counselor_prompt(memory_string: str = "{}") -> dict:
    return {
        "role": "system",
        "content": (
            "You are an AI University Counselor for Gilgit Baltistan students.\n"
            "Your task: Provide FACTUALLY ACCURATE guidance on universities, admissions, and careers.\n\n"
            "TOOLS (Use appropriately):\n"
            "• search_universities: Find REAL universities from database by field/location\n"
            "  → Use for questions about specific universities, programs, or location-based options\n"
            "  → NEVER make up universities - only mention what the tool returns\n"
            "• brave_search: Get current information (exam dates, scholarships, policy changes)\n"
            "  → Use for time-sensitive information NOT about specific universities\n\n"
            "DECISION LOGIC:\n"
            "1. Question about specific universities/programs/locations? → Use search_universities first\n"
            "2. Need current information (dates, announcements)? → Use brave_search\n"
            "3. Vague/general question? → Ask for location, field, and budget BEFORE recommending\n\n"
            "CRITICAL RULES:\n"
            "• ONLY mention universities returned by search_universities tool\n"
            "• Always say: 'Based on our university database...'\n"
            "• If search returns 0 results, tell student honestly - don't invent universities\n"
            "• Never make up admission requirements, test scores, or programs\n"
            "• If unsure about any institution, verify with brave_search first\n\n"
            "STUDENT CONTEXT:\n" + memory_string
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
