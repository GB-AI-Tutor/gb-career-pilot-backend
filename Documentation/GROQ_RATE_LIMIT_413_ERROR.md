# Groq API Rate Limit Error: Request Too Large

## Error Details

```
Error code: 413 - Rate Limit Exceeded (TPM)
{
  'error': {
    'message': 'Request too large for model `llama-3.1-8b-instant`...
               Limit 6000, Requested 9659, please reduce your message size'
  }
}
```

**Limit:** 6000 tokens per minute (TPM)
**Requested:** 9659 tokens
**Overage:** 3659 tokens (61% over limit!)

---

## Root Cause: Oversized System Prompt

### The Problem

The system prompt created by `get_counselor_prompt()` is **extremely verbose** (~2500+ tokens):

**Current Prompt Sections:**
1. Role description (50 tokens)
2. Tool 1 reference with examples (200 tokens)
3. Tool 2 reference with examples (150 tokens)
4. Decision tree (200 tokens)
5. Factual accuracy rules with examples (400 tokens)
6. Response patterns A, B, C with full examples (500 tokens)
7. Student context/memory (variable)
8. Good vs Wrong examples (400 tokens)

**Total System Prompt:** ~2500+ tokens

### Multiple API Calls Compound the Problem

Each message triggers **3 separate Groq API calls**:

```
Message: "Tell me about admission requirements"

├─ CALL 1: Initial decision phase
│  └─ [System Prompt] + [User Message] = ~2600 tokens
│  └─ Status: 200 OK (within limits)
│
├─ CALL 2: If tools triggered (after tool execution)
│  └─ [System Prompt] + [Full Conversation History] + [Tool Results]
│  └─ Status: Could exceed limits if history grows
│
└─ CALL 3: Memory extraction
   └─ [System Prompt] + [Recent Context] + [All Messages]
   └─ Status: 413 ERROR ← HERE (exceeds 6000 TPM)
```

**The Issue:** First message works, but by the **memory extraction call**, accumulated context + system prompt = **9659 tokens**.

---

## Token Breakdown for Your Query

**Estimated token usage:**

```
System Prompt (get_counselor_prompt):        2500 tokens
├─ Tool reference                            200
├─ Decision tree                             200
├─ Factual accuracy rules                    400
├─ Response patterns with examples           500
├─ Good vs wrong examples                    400
└─ Memory context (initially empty)          50

User Message "Tell me about admission...":   15 tokens

Conversation History (built over turns):     ~3000 tokens
├─ First assistant response (clarifying)     200
├─ Tool calls and results (if any)          1500
└─ Other messages in final_history[-4:]     1300

Memory Extraction Prompt:                    500 tokens
├─ Structured extraction instructions        200
└─ Current memory state                      300

Initial Calls:
  Call 1 (Decision): ~2515 tokens ✅ OK (< 6000)

Second Calls (if tools used):
  Call 2 (Tools): ~2515 + history = ~5500 tokens ✅ OK

Third Call (Memory Extraction):
  Call 3 (Memory): 2500 + ~3000 + 500 = ~6000 ✅ OK (borderline)

But with max_tokens=2048 set on streaming calls, the history grows more,
pushing the next memory extraction call to 9659 tokens ❌ EXCEEDED
```

---

## Solution: Compress System Prompt

### Fix 1: Create Two Prompt Versions

**Option A: Use a lean version for memory extraction**

```python
def get_counselor_prompt_lean(memory_string: str = "{}") -> dict:
    """Concise version for memory extraction - only ~500 tokens"""
    return {
        "role": "system",
        "content": (
            "You are an AI University Counselor. Be factually accurate.\n"
            "Use search_universities for university facts, brave_search for current info.\n"
            "Never invent universities.\n\n"
            "MEMORY STATE:\n" + memory_string
        ),
    }
```

**Option B: Conditionally use compact prompt**

```python
# In extract_and_update_memory()
if len(recent_messages) > 2:  # Already have context
    extraction_prompt = get_counselor_prompt_lean()  # Use ~500 token version
else:
    extraction_prompt = get_counselor_prompt()  # Use full version if first message
```

### Fix 2: Refactor Current Prompt (Reduce to ~1200 tokens)

Remove redundant sections:

```python
def get_counselor_prompt(memory_string: str = "{}") -> dict:
    return {
        "role": "system",
        "content": (
            "You are an AI University Counselor for Gilgit Baltistan students.\n"
            "Be FACTUALLY ACCURATE. Only mention universities from search_universities tool.\n"
            "Never invent institutions, programs, or requirements.\n\n"

            "TOOLS:\n"
            "- search_universities: Find real universities by field/location (PRIMARY SOURCE)\n"
            "- brave_search: Get current info (dates, scholarships, policies)\n\n"

            "DECISION TREE:\n"
            "1. Specific university/program/location question? → Use search_universities\n"
            "2. Need current info (dates/scholarships)? → Use brave_search\n"
            "3. Vague question? → Ask for location, field, budget FIRST\n\n"

            "CRITICAL: Always cite 'Based on our database...' if using search results.\n"
            "If database has 0 results, be honest about it.\n\n"

            "STUDENT CONTEXT:\n" + memory_string
        ),
    }
```

**Token Reduction:** 2500 → 800 tokens (-68%)

### Fix 3: Compress Tool Definitions

Move verbose tool descriptions to inline documentation instead of system prompt:

```python
# In ai_tools.py - keep tool definitions lean
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_universities",
            "description": "Find universities in our database",  # ← Short version
            "parameters": {...}
        }
    },
    ...
]
```

---

## Implementation Strategy

### Step 1: Add Token Counting (Diagnostic)

```python
import tiktoken

def estimate_tokens(messages: list, model: str = "gpt-3.5-turbo") -> int:
    """Estimate tokens in message list"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except:
        encoding = tiktoken.get_encoding("cl100k_base")  # Groq uses similar encoding

    total = 0
    for msg in messages:
        if isinstance(msg, dict):
            total += len(encoding.encode(str(msg.get("content", ""))))
    return total

# In extract_and_update_memory():
token_count = estimate_tokens(extraction_history)
logger.warning(f"⚠️ Memory extraction using {token_count} tokens (limit: 6000)")
if token_count > 5500:
    logger.error(f"❌ Will exceed Groq limit! Use lean prompt instead")
```

### Step 2: Use Conditional Prompts

```python
# In extract_and_update_memory():
extraction_history = [extractor_prompt] + recent_messages

# Check if we're approaching limit
token_estimate = estimate_tokens(extraction_history)
if token_estimate > 5000:
    logger.warning(f"⚠️ Switching to lean counselor prompt ({token_estimate} tokens)")
    # Rebuild with lean prompt instead
    lean_system = get_counselor_prompt_lean(memory_string)
    extraction_history = [lean_system] + recent_messages
```

### Step 3: Reduce System Prompt (Recommended)

Replace the current 2500-token prompt with the 800-token version above.

---

## Immediate Fix (Fastest)

Update `get_counselor_prompt()` in [coversation_history.py](src/services/coversation_history.py#L107-L180):

**Before:** ~2500 tokens
**After:** ~800 tokens (68% reduction)

```python
def get_counselor_prompt(memory_string: str = "{}") -> dict:
    return {
        "role": "system",
        "content": (
            "You are an AI University Counselor for Gilgit Baltistan students.\n"
            "Be FACTUALLY ACCURATE. Only mention universities from search_universities tool.\n"
            "Never invent institutions, programs, or requirements.\n\n"

            "TOOLS:\n"
            "- search_universities: Find real universities by field/location (PRIMARY SOURCE)\n"
            "- brave_search: Get current info (dates, scholarships, policies)\n\n"

            "DECISION TREE:\n"
            "1. Specific university/program/location? → Use search_universities\n"
            "2. Need current info? → Use brave_search\n"
            "3. Vague question? → Ask for clarification (location, field, budget)\n\n"

            "RULES:\n"
            "• Always cite: 'Based on our university database...'\n"
            "• If database returns no results, say so honestly\n"
            "• Never make up universities, programs, or admission requirements\n"
            "• If unsure about an institution, verify with brave_search first\n\n"

            "STUDENT CONTEXT:\n" + memory_string
        ),
    }
```

---

## Testing After Fix

### Test 1: Single message within quota
```bash
curl -X POST http://localhost:8000/api/v1/groq/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Tell me about admission requirements"}]}'
# Expected: 200 OK (no 413 error)
```

### Test 2: Multi-turn conversation
```bash
# First message
CONV_ID=$(curl ... | jq .conversation_id)

# Second message with tool-calling expected
curl -X POST http://localhost:8000/api/v1/groq/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "'$CONV_ID'",
    "messages": [{"role": "user", "content": "For CS in Pakistan within 150k"}]
  }'
# Expected: 200 OK, memory updated successfully
```

### Test 3: Check logs for token usage
```bash
tail -f logs/app.log | grep -i "tokens\|memory\|extraction"
# Should see INFO logs, no ERROR about token limits
```

---

## Why This Happened

1. **Ambitious prompt:** Added comprehensive decision trees, examples, and rules to prevent AI hallucination
2. **Multiple API calls:** Each message triggers 2-3 Groq API calls, compounding token usage
3. **Groq 8B limits:** 6000 TPM is quite restrictive for a small model with verbose prompts
4. **No token budgeting:** Didn't account for how system prompt + history would accumulate

---

## Prevention Going Forward

### ✅ DO:
- Keep system prompts under 1000 tokens
- Monitor token usage with logging
- Use different prompts for different tasks (brief for extraction, detailed for main chat)
- Test with max_tokens set (reveals hidden token costs)

### ❌ DON'T:
- Add verbose examples to every prompt
- Repeat the same large system prompt across multiple API calls
- Ignore rate limit warnings

---

## Alternative Solutions (Long-term)

| Solution | Pros | Cons |
|----------|------|------|
| **Upgrade Groq tier** | More tokens/minute | Costs money |
| **Use a larger model** | More context window | Higher latency |
| **Implement prompt caching** | Reduce repeated prompts | Groq may not support yet |
| **Compress prompts (Recommended)** | Fast, free, effective | Requires careful rewriting |
| **Store prompt as vector** | Faster retrieval | Complex architecture |

---

## Summary

| Aspect | Details |
|--------|---------|
| **Error** | 413 Rate Limit - Request too large (9659 > 6000 tokens) |
| **Root Cause** | System prompt is 2500+ tokens + history + multiple API calls |
| **Immediate Fix** | Reduce system prompt from 2500 → 800 tokens (68% reduction) |
| **Files to Modify** | `src/services/coversation_history.py` (get_counselor_prompt) |
| **Testing** | Multi-turn conversation should complete without 413 error |
| **Estimated Impact** | Will reduce total request to ~6000 tokens (within limit) |

**Ready to implement reduced prompt version? This should solve the issue immediately.**
