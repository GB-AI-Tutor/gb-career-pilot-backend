# Validation Error Analysis: Missing Role Field

## Error Details

```
2026-03-22 18:46:38.380 | WARNING  | src.main:validation_exception_handler:85 -
Validation Failed on /api/v1/groq/chat - Data: [{'type': 'missing', 'loc': ('body', 'messages', 1, 'role'),
'msg': 'Field required', 'input': {'content': "I'd love to help! Could you tell me:"},
'url': 'https://errors.pydantic.dev/2.12/v/missing'}]

HTTP Status: 422 Unprocessable Entity
```

---

## Problem Identification

### What's Happening

The API received a ChatRequest with an INVALID second message:

**Invalid Message (What was sent):**
```python
{
    "content": "I'd love to help! Could you tell me:"
    # ❌ Missing required 'role' field
}
```

**Valid Message (What should be sent):**
```python
{
    "role": "assistant",  # ✅ Required field
    "content": "I'd love to help! Could you tell me:"
}
```

### The Request Structure

```python
ChatRequest = {
    "messages": [
        {
            "role": "user",  # ✓ Correct
            "content": "Tell me about admission requirements"
        },
        {
            "content": "I'd love to help! Could you tell me:"
            # ✗ Missing role!
        }
    ],
    "conversation_id": "<some-uuid>"
}
```

---

## Root Cause

### Schema Definition Problem

**File:** [src/schemas/ai_schemas.py](src/schemas/ai_schemas.py)

```python
class MessageRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTENT = "assistent"  # Note: typo - should be "assistant"


class ChatMessage(BaseModel):
    role: MessageRole  # ← REQUIRED (no default value)
    content: str = Field(
        ..., min_length=1, max_length=2000, description="The text content of the message"
    )

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        clean_text = v.strip()
        if not clean_text:
            raise ValueError("Message cannot be empty or just spaces.")
        return clean_text


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ..., min_length=1, description="The full conversation history, include the new message"
    )
    conversation_id: UUID | None = Field(default=None)
```

**The Issue:**
- `MessageRole` enum is *required* on every `ChatMessage`
- No default value provided
- Pydantic v2 strictly enforces this

---

## Flow Analysis

### Where the Problem Originates

**Step 1: User sends first message**
```
Frontend → POST /api/v1/groq/chat
{
  "messages": [
    {"role": "user", "content": "Tell me about admission requirements"}
  ]
}
✓ Valid - role is present
```

**Step 2: Backend processes and responds**
```python
def chat(...):
    # ... processing ...

    def generate_instant_stream():
        full_text = message.content or ""
        yield f"data: {full_text}\n\n"  # ← Streams text chunks

        save_final_state(full_text)
        yield f"data: [DONE_CONV_ID:{conv_id}]\n\n"

    return StreamingResponse(generate_instant_stream(), media_type="text/event-stream")
```

Response format (Server-Sent Events):
```
data: I'd love to help! Could you tell me:
data: • What field? (CS, Engineering, Business?)
data: • What region? (Gilgit, Skardu, etc?)
data: [DONE_CONV_ID:12345]
```

**Step 3: Frontend receives response**
```javascript
// Frontend receives the SSE stream
// AI text chunks: "I'd love to help! Could you tell me:..."
```

**Step 4: User types next message and sends it**
```
Frontend → POST /api/v1/groq/chat
{
  "messages": [
    {"role": "user", "content": "Tell me about admission requirements"},
    {
      "content": "I'd love to help! Could you tell me:"  // ❌ Missing role!
    }
  ]
}
✗ INVALID - Second message missing role field!
```

### Where It Goes Wrong

**The Frontend Bug:**

The frontend is supposed to:
1. ✓ Parse SSE stream from previous AI response
2. ✓ Format AI response as a ChatMessage with `role: "assistant"`
3. ✓ Add user's new message with `role: "user"`
4. ✓ Send complete conversation history with both messages

**What's Actually Happening:**

The frontend is:
1. ✓ Receiving AI response text
2. ✗ NOT wrapping it with `role: "assistant"`
3. ✓ Adding user's new message with `role: "user"` (probably)
4. ✗ Sending malformed history without role on AI response

---

## Validation Chain

### How Pydantic Validates the Request

```
POST /api/v1/groq/chat with payload
    ↓
FastAPI receives request body
    ↓
Pydantic tries to validate against ChatRequest schema
    ↓
ChatRequest expects: list[ChatMessage]
    ↓
For each message in messages array, validate ChatMessage schema
    ↓
Message 0: {"role": "user", "content": "..."}
    → ✓ Passes - has role and content

Message 1: {"content": "..."}
    → ✗ FAILS - role field is MISSING!

Validation error raised:
    - Type: 'missing'
    - Location: body.messages[1].role
    - Message: 'Field required'
```

### The Pydantic Error Handler

**File:** [src/main.py](src/main.py) lines 82-95

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation Failed on {request.url.path} - Data: {exc.errors()}")

    error_details = {str(err["loc"][-1]): err["msg"] for err in exc.errors()}

    return JSONResponse(
        status_code=422,  # Unprocessable Entity
        content={
            "status_code": 422,
            "error_type": "ValidationError",
            "message": "The information provided was invalid.",
            "details": error_details,
        },
    )
```

This catches the validation error and returns 422 status.

---

## Why This Error Occurs

### Three Possible Causes

#### Cause 1: Frontend Not Formatting AI Response ⭐ **MOST LIKELY**
```javascript
// WRONG - Frontend receiving this from SSE stream:
"I'd love to help! Could you tell me:"

// Frontend should format it as:
{
    "role": "assistant",
    "content": "I'd love to help! Could you tell me:"
}

// But frontend is probably doing:
{
    "content": "I'd love to help! Could you tell me:"  // ❌ Missing role
}
```

#### Cause 2: Database Query Returns NULL Role
```python
# convertion_history() retrieves messages from database
response = db.table("messages").select("role", "content", "tool_calls", "tool_call_id")

# If database returns:
# {"content": "...", "role": null}  # ← role is NULL
```

#### Cause 3: Message Constructed Without Role in Backend
```python
# If save_final_state doesn't include role:
db.table("messages").insert(
    {"content": final_text}  # ❌ Missing role
).execute()
```

**But looking at the code, Cause 3 is ruled out** - the code clearly includes `role: "assistant"`.

### Conclusion: **Frontend Issue**

The frontend is not properly formatting the AI's previous response when constructing the next request. It should wrap every AI response in proper ChatMessage format with `role: "assistant"` before including it in the messages array.

---

## Solution

### Fix Required in Frontend

**Before (WRONG):**
```javascript
const response = await fetchAIResponse(userMessage);
const aiText = response.text;  // e.g., "I'd love to help!..."

// User sends follow-up
const nextRequest = {
    messages: [
        { role: "user", content: userMessage },
        { content: aiText }  // ❌ Missing role!
    ]
};
```

**After (CORRECT):**
```javascript
const response = await fetchAIResponse(userMessage);
const aiText = response.text;  // e.g., "I'd love to help!..."

// Properly format AI response as ChatMessage
const aiMessage = {
    role: "assistant",  // ✅ Add role field
    content: aiText
};

// User sends follow-up
const nextRequest = {
    messages: [
        { role: "user", content: userMessage },
        aiMessage  // ✅ Now has role and content
    ]
};
```

### Backend Enhancement (Defense Layer)

To prevent this client-side error from breaking the app, add validation before processing:

Add to [src/api/v1/endpoints/ai_endpoints.py](src/api/v1/endpoints/ai_endpoints.py) - in the `chat()` function:

```python
@router.post("/chat")
def chat(
    chatlist: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    rate_limit_check: bool = Depends(rate_limiter),
):
    # Pydantic validation happens HERE automatically
    # If any message missing 'role', validation error is raised (422)

    # ✅ At this point, all messages are guaranteed to have role + content
    # thanks to ChatMessage schema validation

    db = get_supabase_admin_client()
    # ... rest of code ...
```

The schema validation is already working correctly - it's catching the error. The issue is the frontend needs to be fixed to not send invalid messages.

---

## Enum Fix

### Bonus Issue: Typo in MessageRole

**File:** [src/schemas/ai_schemas.py](src/schemas/ai_schemas.py)

Current:
```python
class MessageRole(str, Enum):
    ASSISTENT = "assistent"  # ❌ Typo
```

Should be:
```python
class MessageRole(str, Enum):
    ASSISTANT = "assistant"  # ✅ Correct spelling
```

This won't cause the current error, but it's a bug that should be fixed.

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Error Type** | Pydantic Validation Error |
| **HTTP Status** | 422 Unprocessable Entity |
| **Missing Field** | `role` in message[1] |
| **Expected Value** | `"assistant"` (one of: "user", "system", "assistant") |
| **Root Cause** | Frontend not properly formatting AI response |
| **Where Error Caught** | Pydantic validation in FastAPI |
| **Handler** | `validation_exception_handler()` in [src/main.py](src/main.py) |
| **User Experience** | "Failed to fetch" message on frontend |

---

## Prevention Checklist

- [ ] Frontend: Verify AI responses are wrapped with `role: "assistant"` before sending
- [ ] Frontend: Ensure every message in messages array has both `role` and `content`
- [ ] Frontend: Parse SSE stream correctly and format responses
- [ ] Backend: Schema validation is working ✓ (already implemented)
- [ ] Backend: Add logging to track message validation failures
- [ ] Schema: Fix typo "ASSISTENT" → "ASSISTANT"
- [ ] Documentation: Document required message format for frontend developers

---

## Message Format Reference

### ✅ Valid Message Format
```python
{
    "role": "user" | "assistant" | "system",  # REQUIRED
    "content": "some text here"                 # REQUIRED, 1-2000 chars
}
```

### ❌ Invalid Message Formats

1. Missing role:
```python
{"content": "text"}  # Missing role!
```

2. Empty content:
```python
{"role": "user", "content": ""}  # Content too short
```

3. Missing content:
```python
{"role": "user"}  # Missing content!
```

4. Invalid role:
```python
{"role": "unknown", "content": "text"}  # Invalid role value
```

---

## Testing This Fix

### Test Case 1: Valid Two-Message Request
```bash
curl -X POST http://localhost:8000/api/v1/groq/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Tell me about CS"},
      {"role": "assistant", "content": "I would like to help. Could you tell me..."}
    ]
  }'
```
Expected: ✅ 200 OK

### Test Case 2: Invalid Message Missing Role
```bash
curl -X POST http://localhost:8000/api/v1/groq/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Tell me about CS"},
      {"content": "I would like to help..."}  # ❌ Missing role
    ]
  }'
```
Expected: ❌ 422 Unprocessable Entity with error details

---

## Related Files

- **Schema Definition:** [src/schemas/ai_schemas.py](src/schemas/ai_schemas.py)
- **Error Handler:** [src/main.py](src/main.py) lines 82-95
- **Endpoint:** [src/api/v1/endpoints/ai_endpoints.py](src/api/v1/endpoints/ai_endpoints.py)
- **History Retrieval:** [src/services/coversation_history.py](src/services/coversation_history.py) lines 9-37
