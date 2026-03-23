# Memory Extraction Error: Missing 'type' Field in Tool Calls

## Error Message
```
Memory update failed: Error code: 400 - {
  'error': {
    'message': "'messages.3' : for 'role:assistant' the following must be satisfied[('messages.3.tool_calls.0.type' : property 'type' is missing)]",
    'type': 'invalid_request_error'
  }
}
```

**Location:** Memory extraction happening after main chat API call completes
**Stage:** `extract_and_update_memory()` function → Groq API call
**Message Index:** messages[3] (4th message, 0-indexed)

---

## Error Flow Diagram

```
User: "For CS in all over Pakistan within 150k"
  ↓
[ai_endpoints.py] First LLM Call
  ├─ Asks clarifying questions (no tool calls)
  ├─ content_text = "I'd love to help!..."
  ├─ message.tool_calls = None (no tools used)
  ↓
[ai_endpoints.py] Streaming Response (Generator B - Instant Stream)
  ├─ Yields response to frontend: "I'd love to help! Could you tell me..."
  ├─ Calls save_final_state(full_text) after streaming completes
  │
  └─→ [ai_endpoints.py line 215] Save Final State
       ├─ Save message to DB: {"role": "assistant", "content": "..."}
       │
       └─→ [ai_endpoints.py line 216] extract_and_update_memory()
           ├─ Receives: recent_context = final_history[-4:] + new_message
           │
           ├─ final_history contains:
           │  ├─ [0] system_prompt
           │  ├─ [1] historical user message: "Tell me about admission requirements"
           │  ├─ [2] historical assistant message: "I'd love to help!..."
           │  │        ↓ THIS MESSAGE HAS TOOL_CALLS (if database had them)
           │  │        └─ tool_calls WITHOUT 'type' field from database ❌
           │  ├─ [3] historical assistant response
           │  └─ [4] new assistant message
           │
           └─→ [coversation_history.py line 71] extract_and_update_memory()
               ├─ Builds extraction_history = [extractor_prompt] + recent_messages
               │  So extraction_history becomes:
               │  ├─ [0] system_prompt (extractor)
               │  ├─ [1] user message from history
               │  ├─ [2] assistant message with CORRUPTED tool_calls
               │  ├─ [3] assistant message with CORRUPTED tool_calls ← ERROR AT INDEX 3
               │  └─ [4] new assistant message
               │
               └─→ Calls Groq API with extraction_history
                   └─ Groq API returns 400: "messages.3.tool_calls.0.type is missing" ❌

```

---

## Root Cause Analysis

### The Problem Chain

1. **Starting Point:** User second message triggers tool-calling scenario
2. **Tool Execution:** First LLM call returns tool_calls for search_universities
3. **Database Storage:** Tool_calls saved to Supabase, but the `type` field might be in database already from previous fixes
4. **Database Retrieval:** `convertion_history()` retrieves messages including those with tool_calls
5. **History Assembly:** `final_history = [system_prompt] + previous_conversations`
6. **Context Building:** `recent_context = final_history[-4:] + [new_message]` ← This includes all messages with potential corrupted tool_calls
7. **Memory Extraction:** `extract_and_update_memory()` is called with `recent_context`
8. **API Call Without Serialization:** Groq API receives messages with tool_calls but WITHOUT cleaning/validation ❌

### Why It Happens

`extract_and_update_memory()` wasn't using `serialize_messages_for_groq()` because:
- It was created before we implemented the serialization solution
- It directly passes messages to Groq API without sanitization
- Messages from `final_history` may contain tool_calls from DATABASE that weren't properly validated

---

## Solution: Two-Layer Fix

### Layer 1: Sanitize Before Passing to extract_and_update_memory()
**Location:** `ai_endpoints.py` line 215

```python
# BEFORE (❌ Unsanitized messages with tool_calls)
recent_context = final_history[-4:] + [{"role": "assistant", "content": final_text}]
extract_and_update_memory(conv_id, recent_context, current_memory, db)

# AFTER (✅ Sanitized messages)
recent_context = serialize_messages_for_groq(final_history[-4:] + [{"role": "assistant", "content": final_text}])
extract_and_update_memory(conv_id, recent_context, current_memory, db)
```

### Layer 2: Sanitize Inside extract_and_update_memory() - Defensive Programming
**Location:** `coversation_history.py` line 71

Add sanitization right before the Groq API call:

```python
# BEFORE (❌ No sanitization)
extraction_history = [extractor_prompt] + recent_messages
response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=extraction_history,  # ← Might have corrupted tool_calls
    response_format={"type": "json_object"},
    temperature=0.1,
)

# AFTER (✅ Sanitized)
extraction_history = [extractor_prompt] + recent_messages
# Ensure all tool_calls have 'type' field
for msg in extraction_history:
    if isinstance(msg, dict) and msg.get("role") == "assistant":
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                if isinstance(tc, dict) and "type" not in tc:
                    tc["type"] = "function"

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=extraction_history,  # ← Now clean
    response_format={"type": "json_object"},
    temperature=0.1,
)
```

---

## Why This Specific Message?

Looking at the error: `messages.3` (4th message in extraction_history)

The structure would be:
```
extraction_history = [
  [0] extractor_prompt (system),
  [1] user message from final_history[-4:],     # "Tell me about admission requirements"
  [2] assistant message from final_history[-4:], # Might have tool_calls from DB ← Could be here
  [3] assistant message from final_history[-4:], # The clarifying response ← ERROR HERE (if had tools)
]
```

The error specifically at [3] suggests the assistant's clarifying response might have had tool_calls saved to the database from an earlier iteration, and those weren't being cleaned.

---

## Testing the Fix

### Test Case 1: Memory Extraction After Tool Calls
```python
# Simulate: Second turn with previous tool call response
previous_response_with_tools = {
    "role": "assistant",
    "content": "Based on the search results...",
    "tool_calls": [
        {
            "id": "call_abc123",
            "function": {"name": "search_universities", "arguments": "{}"}
            # ❌ MISSING 'type' field - this should be caught
        }
    ]
}

# Pass through context
recent_context = [previous_response_with_tools]  # Has corrupted tool_call
extract_and_update_memory(conv_id, recent_context, current_memory, db)

# BEFORE FIX: 400 error on tool_calls.0.type
# AFTER FIX: Should sanitize and succeed
```

### Integration Test
```bash
# 1. Send first message (gets clarification response)
curl -X POST http://localhost:8000/api/v1/groq/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Tell me about admission requirements"}]}'
# Response should be clarifying questions

# 2. Send second message (should trigger tool calls for search)
curl -X POST http://localhost:8000/api/v1/groq/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_id_from_step_1",
    "messages": [{"role": "user", "content": "For CS in all of Pakistan within 150k"}]
  }'

# BEFORE FIX:
# Response 200, but logs show: "Memory update failed: Error code: 400..."
# AFTER FIX:
# Response 200, memory successfully updated, no error logs
```

---

## Files Modified

| File | Location | Change |
|------|----------|--------|
| `ai_endpoints.py` | Line 215 | Serialize recent_context before passing to extract_and_update_memory() |
| `coversation_history.py` | Line 71 | Add 'type' field validation to tool_calls in extraction_history |

---

## Related Issues

This error is similar to previous `type` field errors but manifests in a different layer:

| Layer | Error | Solution |
|-------|-------|----------|
| **Retrieval** (convertion_history) | Tool_calls missing 'type' when retrieved from DB | Validate in convertion_history() ✅ Already done |
| **API Serialization** (main chat) | Pydantic models include unsupported fields | Use serialize_messages_for_groq() ✅ Already done |
| **Memory Extraction** (extract_and_update_memory) | Recent context includes tool_calls without 'type' | ← **THIS IS THE NEW ONE** |

---

## Summary

| Aspect | Details |
|--------|---------|
| **Error** | 400 Groq API: `messages.3.tool_calls.0.type is missing` |
| **Location** | `extract_and_update_memory()` → Groq API call |
| **Root Cause** | Messages with tool_calls passed without sanitization |
| **Root Source** | `ai_endpoints.py` line 215: `recent_context = final_history[-4:]` includes messages with corrupted tool_calls from database |
| **Solution** | Two-layer sanitization: (1) Sanitize before passing, (2) Validate inside function (defensive) |
| **Files Modified** | `ai_endpoints.py` (1 location), `coversation_history.py` (1 location) |
| **Testing** | Multi-turn conversation with tool calls should complete without error logs |

**Status:** Ready to implement (see fixes below)
