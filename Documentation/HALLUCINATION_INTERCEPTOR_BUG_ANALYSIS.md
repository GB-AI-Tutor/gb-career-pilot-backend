# Bug Analysis: Hallucination Leaking to Frontend

## Problem Statement

When a user asks "Tell me about admission requirements", they receive a response like:

```
It seems like I couldn't find any universities in Gilgit Baltistan matching your specified criteria.
I'll try an alternative search method to find more information.
<function=brave_search>{"query":"admission requirements for computer science in Gilgit Baltistan","num_results":3}</function>
```

**Issue:** The hallucinated function call XML is **visible in the frontend response** instead of being intercepted and processed as a proper tool call.

---

## Root Cause Analysis

### What's Happening

1. **LLM Hallucination:** Groq LLM generates text that includes an XML-like function call because:
   - The model is instructed to use tools but doesn't properly call `tool_choice="auto"`
   - Instead of creating proper `tool_calls`, it hallucinates function calls in the text
   - Example: `<function=brave_search>{"query":"...","num_results":3}</function>`

2. **Incomplete Hallucination Detection:** The interceptor code (lines 91-129) has multiple issues:

   **Issue A: Regex Pattern May Not Match All Formats**
   ```python
   pattern = r"<.*?function=([^>]+)>(.*?)</function>"
   matches = re.findall(pattern, content_text)
   ```

   - Pattern expects: `<...function=NAME>ARGS</function>`
   - Your example matches, but it might fail on variations:
     - `<function =brave_search>` (space before =)
     - `<function_call>` (different tag name)
     - Missing closing tags
     - Different argument wrapping

   **Issue B: No Fallback Cleaning**
   ```python
   if not message.tool_calls and "function=" in content_text:
       pattern = r"<.*?function=([^>]+)>(.*?)</function>"
       matches = re.findall(pattern, content_text)

       if matches:
           # ... create mock tool calls ...
           message.content = None  # ✅ Content cleaned if regex matches
       # ❌ BUT: If regex doesn't match, content_text stays unchanged!
   ```

3. **Content Sent to Frontend Unclean:**
   - When regex doesn't match, `message.content` still contains the hallucinated call
   - The else branch (line 217) sends raw content: `full_text = message.content or ""`
   - Hallucinated function call appears in frontend

### Code Flow Visualization

```
┌─────────────────────────────────────────┐
│  LLM Response with Hallucination        │
│  Content: "...find information.         │
│  <function=brave_search>...</function>" │
└─────────────────┬───────────────────────┘
                  │
                  v
        ┌─────────────────────┐
        │ message.tool_calls  │ = None (no proper tool calls)
        │ "function=" in text │ = True ✓
        └──────────┬──────────┘
                   │
                   v
        ┌──────────────────────────────┐
        │ Try Regex Match              │
        │ Pattern: <.*?function=...>   │
        └────┬──────────────────┬──────┘
             │                  │
        Matches          Doesn't Match (varies)
             │                  │
             v                  v
      ✅ Create Mock      ❌ Content unchanged
         Tool Calls       message.content has
      message.content      hallucinated text
      = None                   │
                               v
                        SENT TO FRONTEND
                        (User sees XML!)
```

---

## Issues Identified

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | Regex pattern too strict, doesn't match all hallucination formats | High | Function calls leak to frontend |
| 2 | No error handling if regex doesn't match | High | Content is sent unchanged |
| 3 | Pattern only looks for `<function=` format | Medium | Other hallucination patterns not caught |
| 4 | Stripping function call from content_text not done | Medium | Raw text with XML sent to user |
| 5 | No logging of detected hallucinations | Low | Hard to debug when it happens |

---

## Solution

### Fix 1: Robust Hallucination Detection with Fallback Cleaning

**Replace the hallucination interceptor (lines 91-129) with:**

```python
# --- 🛡️ THE HALLUCINATION INTERCEPTOR (IMPROVED) ---
if not message.tool_calls and content_text and "function=" in content_text:
    pattern = r"<\s*function\s*=\s*([^>]+)>(.*?)</function>"
    matches = re.findall(pattern, content_text, re.DOTALL)

    if matches:
        logger.info(f"🚨 Hallucination detected: {len(matches)} function call(s)")

        class MockFunction(BaseModel):
            name: str
            arguments: str

        class MockToolCall(BaseModel):
            id: str
            function: MockFunction
            type: str = "function"

            def model_dump(self):
                return {
                    "id": self.id,
                    "type": self.type,
                    "function": {
                        "name": self.function.name,
                        "arguments": self.function.arguments,
                    },
                }

        mock_tool_calls = [
            MockToolCall(
                id=f"call_{uuid.uuid4().hex[:4]}",
                function=MockFunction(name=n.strip(), arguments=a.strip())
            )
            for n, a in matches
        ]

        # Strip ALL function call patterns from content
        cleaned_content = re.sub(
            r"<\s*function\s*=\s*[^>]+>(.*?)</function>",
            "",
            content_text,
            flags=re.DOTALL
        ).strip()

        message.tool_calls = mock_tool_calls
        message.content = cleaned_content if cleaned_content else None
        logger.info(f"✅ Converted to {len(mock_tool_calls)} tool call(s)")
    else:
        # Regex didn't match but "function=" is in text - clean it anyway
        if "<" in content_text and ">" in content_text:
            logger.warning("⚠️ Possible function call not caught by regex")
            # Clean content by removing anything that looks like XML tags
            # with 'function' in them
            cleaned = re.sub(r"<[^>]*function[^>]*>.*?</[^>]*function[^>]*>", "", content_text, flags=re.DOTALL)
            if cleaned != content_text:
                message.content = cleaned.strip() or None
                logger.info("✅ Cleaned suspicious XML patterns")
# ----------------------------------------
```

### Fix 2: Alternative - Use Better LLM Instructions

Prevent hallucinations in the first place by improving system prompt. Add to your system prompt:

```python
# In get_counselor_prompt():
"""
IMPORTANT: Only call tools when you have ALL required information:
- For university search: call search_universities with specific criteria
- For external research: call brave_search with clear query

DO NOT:
- Make up function calls in XML format
- Use <function=...> tags in your response
- Pretend to call tools without the proper format

If you cannot call a real tool, explain this clearly to the user.
"""
```

### Fix 3: Frontend Defense Layer

Add client-side validation to strip any remaining leaked function calls:

```javascript
// In your frontend response handler
function cleanResponse(text) {
    // Remove any XML-like function calls that leaked through
    return text
        .replace(/<\s*function\s*=\s*[^>]+>.*?<\/\s*function\s*>/gi, '')
        .trim();
}
```

---

## Testing the Fix

### Test Case 1: Exact Format (Should Catch)
```
Input: "I'll search now. <function=brave_search>{"query":"admission"}</function> Done."
Expected: Mock tool call created, content cleaned ✓
```

### Test Case 2: Spaces in Format (Improved Pattern Catches)
```
Input: "I'll search. <function = brave_search > {...} </function> Thanks."
Expected: Mock tool call created, content cleaned ✓
```

### Test Case 3: Malformed Format (Fallback Cleans)
```
Input: "Let me search<function=search>data</function>here"
Expected: Recognized as hallucination, content partially cleaned ✓
```

---

## Why This Happens

This is a known LLM limitation called **"hallucinated function calls"**:
- Small models (7B-8B parameters) like Groq's Llama 3.1 sometimes generate function call syntax in their responses
- They don't understand that function calls must be structured objects, not text
- This is less common in larger models (70B+) but still occurs

**Prevention Strategy:**
1. ✅ Explicit system prompts (what we added)
2. ✅ Robust detection (what we're fixing)
3. ✅ Clean output before sending (what we're implementing)
4. ✅ Log hallucinations (for monitoring)

---

## Files Affected

- [src/api/v1/endpoints/ai_endpoints.py](src/api/v1/endpoints/ai_endpoints.py) - Lines 91-129 (interceptor)
