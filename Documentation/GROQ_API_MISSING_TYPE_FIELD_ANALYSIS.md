# Groq API Error Analysis: Missing 'type' Field in Tool Calls

## Error Details

```
groq.BadRequestError: Error code: 400
{
  'error': {
    'message': "'messages.2' : for 'role:assistant' the following must be satisfied[('messages.2.tool_calls.0.type' : property 'type' is missing)]",
    'type': 'invalid_request_error'
  }
}
```

---

## Problem Identification

### What's Happening

The Groq API received a message with incomplete tool_call objects:

**Invalid Format (What was sent):**
```python
message[2] = {
    "role": "assistant",
    "content": "...",
    "tool_calls": [
        {
            "id": "call_xyz123",
            "function": {
                "name": "search_universities",
                "arguments": "{...}"
            }
            # ❌ Missing 'type' field!
        }
    ]
}
```

**Valid Format (What Groq expects):**
```python
message[2] = {
    "role": "assistant",
    "content": "...",
    "tool_calls": [
        {
            "type": "function",  # ← REQUIRED at root level
            "id": "call_xyz123",
            "function": {
                "name": "search_universities",
                "arguments": "{...}"
            }
        }
    ]
}
```

### Message Index Details

| Index | Message | Expected |
|-------|---------|----------|
| 0 | System prompt | `role: "system"` |
| 1 | User question or previous context | `role: "user"` or from history |
| 2 | AI response with tool calls | `role: "assistant"` + **tool_calls with 'type'** ❌ Missing |

---

## Root Cause Analysis

### Issue #1: Tool Calls Missing 'type' When Retrieved from Database

**Where the problem starts:**

[src/services/coversation_history.py](src/services/coversation_history.py) - Lines 9-40:

```python
def convertion_history(conversation_id: UUID, limit_count: int = 15):
    response = db.table("messages").select(
        "role", "content", "tool_calls", "tool_call_id"
    ).execute()

    # tool_calls retrieved as raw JSON from database
    # If 'type' wasn't stored, it won't be in the JSON

    cleaned_history = []
    for msg in history:
        cleaned_msg = {"role": msg["role"], "content": msg["content"]}

        if msg["role"] == "assistant" and msg.get("tool_calls"):
            cleaned_msg["tool_calls"] = msg["tool_calls"]  # ← As-is from DB, may be incomplete

        cleaned_history.append(cleaned_msg)

    return cleaned_history
```

**The Problem:**
- Tool calls are stored as JSON in the database
- If the 'type' field wasn't explicitly saved, database returns it without 'type'
- The code doesn't validate or add missing 'type' field
- When sent to Groq, validation fails

---

### Issue #2: Pydantic Models Not Serialized to Plain Dicts Before Sending to Groq

**Where it happens:**

[src/api/v1/endpoints/ai_endpoints.py](src/api/v1/endpoints/ai_endpoints.py) - Line 198-201:

```python
final_history.extend(
    [
        message,  # ← This is a Pydantic BaseModel or message object
        {        # ← This is a plain dict (correct)
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result),
        },
    ]
)
```

When `message` (a Pydantic model) is added directly to `final_history`, it may not serialize completely, missing the 'type' field in nested tool_calls.

---

### Issue #3: Tool Call Creation Missing Explicit 'type'

When tool calls are created or reconstructed, the 'type' field might not be explicitly preserved.

---

## Data Flow Showing Where 'type' Is Lost

```
┌─────────────────────────────────────────────────────┐
│ Step 1: Tool Call Created with Type Field          │
│ (MockToolCall in hallucination interceptor)         │
├─────────────────────────────────────────────────────┤
│ {                                                   │
│   "type": "function",  ← ✓ Present here             │
│   "id": "call_xyz",                                 │
│   "function": { "name": "...", "arguments": "..." } │
│ }                                                   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ Step 2: Tool Call Saved to Database                │
│ (Using model_dump())                               │
├─────────────────────────────────────────────────────┤
│ db.table("messages").insert({                       │
│   "role": "assistant",                              │
│   "tool_calls": [t.model_dump() for t in ...]      │
│   "type": "function" ← Included in JSON             │
│ }                                                   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ Step 3: Tool Call Retrieved from Database          │
│ (Depending on how DB returns JSON)                 │
├─────────────────────────────────────────────────────┤
│ Query: SELECT tool_calls FROM messages              │
│ Returns: tool_calls JSON as-is                      │
│                                                     │
│ Possible Issue:                                     │
│ - If database column stores JSON, it might strip    │
│   fields or not preserve 'type'                     │
│ - convertion_history just passes it through        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ Step 4: Tool Calls Added to final_history          │
│ (Lines 198-201 in ai_endpoints.py)                 │
├─────────────────────────────────────────────────────┤
│ final_history.extend([                              │
│   message,  ← May have tool_calls without 'type'   │
│   {"role": "tool", ...}                             │
│ ])                                                  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ Step 5: Messages Sent to Groq API                  │
│ (Line 222 in ai_endpoints.py)                      │
├─────────────────────────────────────────────────────┤
│ client.chat.completions.create(                     │
│   messages=final_history,  ← Missing 'type' field! │
│ )                                                   │
│                                                     │
│ ❌ Groq rejects: "messages.2.tool_calls.0.type"   │
│    is missing                                       │
└─────────────────────────────────────────────────────┘
```

---

## Solution: Three-Layer Fix

### Layer 1: Ensure Tool Calls Have 'type' When Saved

**File:** [src/api/v1/endpoints/ai_endpoints.py](src/api/v1/endpoints/ai_endpoints.py)

After tool_calls are retrieved from the LLM but before saving to database:

```python
# When saving tool calls to database
tool_calls_for_db = []
for t in message.tool_calls:
    tc = t.model_dump()
    # Ensure 'type' field is always present
    if "type" not in tc:
        tc["type"] = "function"
    tool_calls_for_db.append(tc)

db.table("messages").insert({
    "conversation_id": conv_id,
    "role": "assistant",
    "content": message.content or "",
    "tool_calls": tool_calls_for_db,  # ← With type field guaranteed
}).execute()
```

### Layer 2: Reconstruct 'type' Field When Retrieved

**File:** [src/services/coversation_history.py](src/services/coversation_history.py)

When retrieving tool_calls from database, ensure 'type' field exists:

```python
def convertion_history(conversation_id: UUID, limit_count: int = 15):
    response = db.table("messages").select(
        "role", "content", "tool_calls", "tool_call_id"
    ).eq("conversation_id", conversation_id).order("created_at", desc=True).limit(limit_count).execute()

    history = response.data
    history.reverse()

    cleaned_history = []
    for msg in history:
        cleaned_msg = {"role": msg["role"], "content": msg["content"]}

        # Include and validate tool_calls for assistant messages
        if msg["role"] == "assistant" and msg.get("tool_calls"):
            tool_calls = msg["tool_calls"]

            # Ensure each tool_call has 'type' field
            validated_tool_calls = []
            for tc in tool_calls:
                if isinstance(tc, dict):
                    if "type" not in tc:
                        tc["type"] = "function"  # Default for function calls
                    validated_tool_calls.append(tc)

            cleaned_msg["tool_calls"] = validated_tool_calls

        # Include tool_call_id for tool messages
        if msg["role"] == "tool" and msg.get("tool_call_id"):
            cleaned_msg["tool_call_id"] = msg["tool_call_id"]

        cleaned_history.append(cleaned_msg)

    return cleaned_history
```

### Layer 3: Ensure Proper Serialization Before Sending to Groq

**File:** [src/api/v1/endpoints/ai_endpoints.py](src/api/v1/endpoints/ai_endpoints.py)

Convert all Pydantic models to plain dicts before sending:

```python
# Before sending to Groq, convert all messages to plain dicts
def serialize_message_for_groq(msg):
    """Convert message (Pydantic model or dict) to plain dict for API"""
    if hasattr(msg, 'model_dump'):
        # It's a Pydantic model
        return msg.model_dump()
    elif isinstance(msg, dict):
        # Already a dict, ensure tool_calls have 'type' field
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg.get("tool_calls", []):
                if "type" not in tc:
                    tc["type"] = "function"
        return msg
    else:
        return msg

# Serialize final_history before sending to Groq
serialized_history = [serialize_message_for_groq(msg) for msg in final_history]

# Send to Groq with serialized messages
final_response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=serialized_history,  # ← Properly serialized
    stream=True,
)
```

---

## Expected Tool Call Format for Groq

### Correct Structure

```python
{
    "role": "assistant",
    "content": null,  # Can be null if tool_calls present
    "tool_calls": [
        {
            "type": "function",              # ← REQUIRED at root
            "id": "call_abc123xyz",         # ← Unique identifier
            "function": {
                "name": "search_universities",  # ← Tool name
                "arguments": "{\"...\":\"...\"}"  # ← JSON string
            }
        }
    ]
}
```

### What Was Sent (Broken)

```python
{
    "role": "assistant",
    "content": null,
    "tool_calls": [
        {
            # ❌ Missing: "type": "function"
            "id": "call_abc123xyz",
            "function": {
                "name": "search_universities",
                "arguments": "{\"...\":\"...\"}"
            }
        }
    ]
}
```

---

## Implementation Priority

### Critical (Must Fix Immediately)

1. ✅ **Layer 2:** Add type validation in `convertion_history()`
   - Ensures retrieved tool_calls always have 'type' field
   - Prevents Groq validation errors

2. ✅ **Layer 3:** Serialize messages before sending to Groq
   - Converts Pydantic models to plain dicts
   - Ensures completeness of all fields

### Important (Should Fix)

3. **Layer 1:** Validate tool_calls when saving
   - Prevents incomplete data in database

### Nice to Have

4. Add logging to track tool_call serialization
5. Add validation middleware for API responses

---

## Testing

### Test Case 1: Tool Call with Missing Type
```bash
# This should fail with current code
curl -X POST http://localhost:8000/api/v1/groq/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What universities in Gilgit for CS?"}
    ]
  }'

# Expected: Should call search_universities, include 'type' field in tool_calls
```

### Test Case 2: Multi-Turn Conversation with Tool Calls
```bash
# First turn
POST /api/v1/groq/chat - "What universities in Gilgit for CS?"
Response: Tool calls made with 'type' field

# Second turn with previous messages
POST /api/v1/groq/chat - Full history with tool_calls
Message history includes tool_calls with 'type' field
Expected: No Groq validation error
```

---

## Related Files

- **Endpoint:** [src/api/v1/endpoints/ai_endpoints.py](src/api/v1/endpoints/ai_endpoints.py)
  - Line 170-180: Tool call saving
  - Line 198-201: Tool call addition to history
  - Line 217-225: Sending to Groq

- **History:** [src/services/coversation_history.py](src/services/coversation_history.py)
  - Line 9-40: Tool call retrieval and validation

- **Schema:** [src/schemas/ai_schemas.py](src/schemas/ai_schemas.py)
  - ChatMessage definition

---

## Groq API Documentation Reference

According to OpenAI API (Groq uses compatible format):

```
Tool calls array format:
[
  {
    "id": "call_abc123",
    "type": "function",  # ← Always required: "function"
    "function": {
      "name": "function_name",
      "arguments": "{\"param\":\"value\"}"  # ← JSON string, not object
    }
  }
]
```

The 'type' field at the root level of tool_call is **mandatory** in the OpenAI/Groq API spec.

---

## Summary

| Aspect | Issue | Fix |
|--------|-------|-----|
| **Error** | Missing 'type' in tool_calls | Add validation |
| **Location** | message[2].tool_calls[0].type | Groq API requirement |
| **Root Cause** | Tool calls retrieved without 'type' field | Database retrieval incomplete |
| **Layer 1 Fix** | Validate when saving | Ensure 'type' in database |
| **Layer 2 Fix** | Validate when retrieving | Reconstruct missing 'type' |
| **Layer 3 Fix** | Serialize before Groq | Convert models to dicts |
| **Priority** | Critical | Must fix for tool calling |
