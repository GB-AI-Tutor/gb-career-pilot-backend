# Advanced Methods to Keep Detailed Prompts Without Token Bloat

There are **several approaches** beyond simple compression. Let me show you the best options for your use case.

---

## Option 1: Conditional/Dynamic Prompts (Recommended)

**Concept:** Use different prompts based on conversation context - detailed only when needed.

### Implementation

```python
def get_counselor_prompt(memory_string: str = "{}") -> dict:
    """
    Adapt prompt size based on conversation state.
    First message = detailed, subsequent messages = lean
    """
    memory = json.loads(memory_string) if memory_string != "{}" else {}

    # If student hasn't specified location/field yet, we need guidance
    if not memory.get("location_preferences") or not memory.get("academic_goals"):
        return {
            "role": "system",
            "content": (
                "You are an AI University Counselor for Gilgit Baltistan.\n"
                "Always ask for: field, location, and budget BEFORE recommending universities.\n"
                "Use search_universities tool for specific location/program queries.\n"
                "Never invent universities - only mention what the tool returns.\n"
                "Be concise and helpful.\n"
            ),
        }
    else:
        # Already have context, use minimal prompt
        return {
            "role": "system",
            "content": (
                "You are an AI University Counselor.\n"
                "Student context: " + memory_string + "\n"
                "Use search_universities for university facts.\n"
                "Never invent information.\n"
            ),
        }
```

**Pros:**
- Keeps early conversations lean (~200 tokens)
- Gradually provides context as memory builds
- No repeated verbose instructions after first message

**Cons:**
- Need to track conversation state
- AI behavior changes slightly between turns

**Token Savings:** First call ~200 tokens → Later calls ~150 tokens

---

## Option 2: Few-Shot Learning Instead of Rules

**Concept:** Show examples instead of explaining rules. Modern LLMs learn from examples faster than rules.

### Before (Verbose Rules - 800 tokens)
```python
"CRITICAL RULES:\n"
"• ONLY mention universities returned by search_universities tool\n"
"• Always say: 'Based on our university database...'\n"
"• If search returns 0 results, tell student honestly - don't invent universities\n"
"... 20 more rules ...\n"
```

### After (Examples - 300 tokens)
```python
{
    "role": "system",
    "content": "You are an AI University Counselor. Be accurate. Use search_universities for facts."
},
{
    "role": "user",
    "content": "What universities offer CS in Pakistan?"
},
{
    "role": "assistant",
    "content": "Let me find Computer Science programs for you... [calls search_universities]\nBased on our university database, here are the verified options: [shows results only]"
},
{
    "role": "user",
    "content": "I want to study at a fake university"
},
{
    "role": "assistant",
    "content": "I can't find that university in our database. Would you like me to search for similar programs in verified institutions?"
}
```

**How it works:**
- Instead of telling AI "never make up universities"
- Show it an actual example conversation where it handles this correctly
- LLIs learn patterns from examples 5-10x faster than rules

**Pros:**
- 60% smaller prompt (~300 tokens vs 800)
- AI actually performs BETTER with good examples
- Works across different LLM sizes

**Cons:**
- Need 3-5 good example pairs
- Takes more iterations to perfect

**Token Savings:** ~500 tokens per message

---

## Option 3: Retrieval-Augmented Prompting (Advanced)

**Concept:** Store detailed rules in database, retrieve only relevant ones per query.

### Architecture

```python
# 1. Store rules in database (one-time)
RULES_DB = {
    "university_accuracy": {
        "tokens": 150,
        "content": "Only mention universities from search_universities tool...",
        "triggers": ["university", "college", "institution"]
    },
    "admission_info": {
        "tokens": 100,
        "content": "Never invent admission requirements...",
        "triggers": ["admission", "requirement", "criteria"]
    },
    "tool_usage": {
        "tokens": 120,
        "content": "Use search_universities for location/program queries...",
        "triggers": ["tool", "search", "find"]
    }
}

# 2. Retrieve only relevant rules for this query
def get_dynamic_prompt(user_query: str, memory: dict) -> dict:
    """Retrieve only rules relevant to this specific query"""

    relevant_rules = []
    for rule_name, rule_data in RULES_DB.items():
        # Check if any trigger keyword appears in user query
        if any(trigger in user_query.lower() for trigger in rule_data["triggers"]):
            relevant_rules.append(rule_data["content"])

    # Build prompt with only relevant rules
    rules_section = "\n".join(relevant_rules) if relevant_rules else "Be helpful and accurate."

    return {
        "role": "system",
        "content": (
            "You are an AI University Counselor.\n"
            "RELEVANT RULES FOR THIS QUERY:\n" +
            rules_section + "\n\n"
            "STUDENT CONTEXT:\n" +
            json.dumps(memory)
        ),
    }

# Usage
prompt = get_dynamic_prompt("What CS universities are in Gilgit?", current_memory)
```

**Pros:**
- Adapts prompt to specific query type
- Only includes relevant rules (~300 tokens max)
- Highly scalable for complex systems
- Perfect for large rule sets

**Cons:**
- More complex to implement
- Requires trigger keyword tuning
- Needs database setup

**Token Savings:** ~400-500 tokens per message (only use what's needed)

---

## Option 4: Prompt Compression Techniques

### 4A: Abbreviation-Based (Light Compression)

```python
# CONVERT:
"CRITICAL RULES:\n"
"• ONLY mention universities returned by search_universities tool\n"
"• Always say: 'Based on our university database...'\n"

# TO:
"RULES:\n"
"[1] Mention ⊆ search_universities() output\n"
"[2] Cite: 'Based on our DB...'\n"
```

**Token Reduction:** ~20% (not much)

### 4B: Schema-Based Encoding (Better)

```python
# Instead of natural language rules
prompt = {
    "role": "system",
    "instructions": [
        {"domain": "universities", "constraint": "database_only", "action": "verify_with_tool"},
        {"domain": "admission", "constraint": "no_fabrication", "action": "ask_or_search"},
        {"domain": "tools", "constraint": "use_appropriately", "action": "match_query_type"}
    ]
}
```

**Token Reduction:** ~30% (AI parses structure efficiently)

### 4C: Instruction Hierarchy (Best)

Group rules by priority, only include top-tier:

```python
RULES_BY_PRIORITY = {
    "CRITICAL": [  # Always include
        "Never invent universities",
        "Use search_universities for facts"
    ],
    "IMPORTANT": [  # Include if space available
        "Ask for clarification on vague queries",
        "Cite database sources"
    ],
    "NICE_TO_HAVE": [  # Optional
        "Explain why you're using each tool",
        "Provide reasoning for recommendations"
    ]
}

def build_prompt(max_tokens: int = 500, memory_string: str = "{}") -> dict:
    """Build prompt within token budget"""
    content = "You are an AI University Counselor.\n\n"
    estimated_tokens = 50

    # Add CRITICAL rules
    for rule in RULES_BY_PRIORITY["CRITICAL"]:
        estimated_tokens += len(rule) // 4  # Rough estimate
        content += f"• {rule}\n"

    # Add IMPORTANT if space allows
    if estimated_tokens < max_tokens - 200:
        for rule in RULES_BY_PRIORITY["IMPORTANT"]:
            estimated_tokens += len(rule) // 4
            content += f"• {rule}\n"

    # Add memory
    content += "\nSTUDENT CONTEXT:\n" + memory_string

    return {"role": "system", "content": content}
```

**Token Savings:** Scales dynamically, stays under budget

---

## Option 5: Prompt Chaining (Different Approach)

**Concept:** Instead of one large prompt, break into multiple focused smaller requests.

### Example: Sequential Tool Calls

```python
# INSTEAD OF: One call with huge prompt about all rules
# DO THIS: Three focused calls

async def handle_user_query(user_message: str, conv_id: UUID):

    # Step 1: Classify query (~500 tokens total)
    classification = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Classify this query type. Reply: UNIVERSITY, ADMISSION, or GENERAL"},
            {"role": "user", "content": user_message}
        ]
    )
    query_type = classification.choices[0].message.content

    # Step 2: Use appropriate tool (~400 tokens total)
    if query_type == "UNIVERSITY":
        tool_result = search_universities_with_context(user_message)
    elif query_type == "ADMISSION":
        tool_result = get_admission_info(user_message)
    else:
        tool_result = get_general_guidance(user_message)

    # Step 3: Generate response with context (~500 tokens total)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful counselor"},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": f"Found: {tool_result}"},
            {"role": "user", "content": "Now provide detailed guidance based on this"}
        ]
    )

    return response.choices[0].message.content

# Total: 3 × 500 = 1500 tokens spread across calls
# vs. 1 × 2000 = 2000 tokens in single call + TPM limits
```

**Pros:**
- Fits within TPM limits (6000/3 = 2000 per call)
- Each step is optimized for its task
- Easier to add error handling between steps

**Cons:**
- 3 API calls = 3x latency (worse UX)
- More complex code
- Higher costs (but same total tokens)

---

## Option 6: Hybrid: Caching + Compression (Best of Both Worlds)

**Concept:** Compress prompt BUT reuse across multiple messages using caching.

```python
import hashlib

# Cache the compressed prompt
PROMPT_CACHE = {}

def get_cached_prompt(memory_string: str = "{}") -> tuple[dict, str]:
    """Return prompt + cache_key"""

    # Generate cache key from memory
    cache_key = hashlib.md5(memory_string.encode()).hexdigest()

    if cache_key in PROMPT_CACHE:
        return PROMPT_CACHE[cache_key], cache_key

    # Build compressed prompt (700 tokens)
    prompt = {
        "role": "system",
        "content": (
            "You are an AI University Counselor.\n"
            "• Use search_universities for university facts\n"
            "• Never invent institutions\n"
            "• Ask for location/field if vague\n\n"
            "STUDENT CONTEXT:\n" + memory_string
        )
    }

    # Cache it
    PROMPT_CACHE[cache_key] = prompt

    return prompt, cache_key

# Usage in chat endpoint
def chat(conv_id: UUID, user_message: str):
    memory = get_conversation_memory(conv_id)  # Usually ~50 tokens

    # Reuse same prompt for this conversation
    system_prompt, _ = get_cached_prompt(json.dumps(memory))

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[system_prompt] + get_history(conv_id),
        # If Groq supports caching:
        # cache_control={"type": "ephemeral"}  # Keep in cache for 1 hour
    )
```

**Pros:**
- Compressed prompt (700 tokens)
- Cached across multiple messages in same conversation
- No repeated system prompt costs in multi-turn

**Cons:**
- Requires Groq caching API (may not be available yet)
- Need to manage cache lifecycle

**Token Savings:** 700 tokens on first call → 0 tokens on subsequent calls (if cached)

---

## Option 7: Vector Embeddings + Retrieval (Advanced)

**Concept:** Embed rules as vectors, retrieve similar rules only when needed.

```python
import numpy as np
from sklearn.metrics.cosine_similarity import cosine_similarity

# 1. Pre-encode all rules
RULES = {
    "r1": {"text": "Never invent universities", "embedding": embed("..."), "tokens": 10},
    "r2": {"text": "Use search_universities for facts", "embedding": embed("..."), "tokens": 15},
    # ... 20 more rules ...
}

def get_relevant_rules(user_query: str, max_tokens: int = 300) -> list[str]:
    """Retrieve only rules similar to user query"""

    query_embedding = embed(user_query)
    similarities = []

    for rule_id, rule_data in RULES.items():
        sim = cosine_similarity(query_embedding, rule_data["embedding"])
        similarities.append((rule_id, sim, rule_data["tokens"]))

    # Sort by relevance
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Include rules while under token budget
    selected_rules = []
    total_tokens = 0
    for rule_id, sim, tokens in similarities:
        if total_tokens + tokens <= max_tokens and sim > 0.3:  # Relevance threshold
            selected_rules.append(RULES[rule_id]["text"])
            total_tokens += tokens

    return selected_rules

# Usage
query = "What universities offer CS in Gilgit?"
relevant_rules = get_relevant_rules(query)  # Returns only ~150 tokens of relevant rules
prompt = build_prompt_with_rules(relevant_rules)
```

**Pros:**
- Highly intelligent rule selection
- Scales to 100+ rules without bloat
- Context-aware

**Cons:**
- Complex setup (need embeddings)
- Slower (embedding lookup)
- Overkill for <20 rules

---

## Comparison Table

| Method | Overhead | Quality | Complexity | Best For |
|--------|----------|---------|-----------|----------|
| **Conditional Prompts** | 150-200 tokens | ⭐⭐⭐⭐ | Low | Multi-turn conversations ✅ |
| **Few-Shot Examples** | 300 tokens | ⭐⭐⭐⭐⭐ | Medium | Consistent behavior |
| **Dynamic Retrieval** | 200-400 tokens | ⭐⭐⭐⭐ | High | Large rule sets |
| **Compression** | 700 tokens | ⭐⭐⭐ | Low | Quick fix |
| **Prompt Chaining** | 1500 tokens | ⭐⭐⭐ | High | Complex workflows |
| **Caching** | 0 (cached) | ⭐⭐⭐⭐ | Medium | Long conversations |
| **Vector Retrieval** | 150-300 tokens | ⭐⭐⭐⭐⭐ | Very High | 50+ rules |

---

## **My Recommendation for Your Use Case**

**Start with Option 1 + Option 2 (Conditional + Few-Shot):**

```python
def get_counselor_prompt(memory_string: str = "{}") -> list[dict]:
    """Return message list with system + examples"""

    memory = json.loads(memory_string) if memory_string != "{}" else {}

    # System prompt: minimal but clear
    system_msg = {
        "role": "system",
        "content": (
            "You are an AI University Counselor for Gilgit Baltistan students.\n"
            "Be factually accurate. Use search_universities for university facts.\n"
            "Never invent institutions or requirements.\n"
            "Ask for location/field/budget clarification before recommending.\n"
        )
    }

    # Example pairs: show correct behavior (instead of explaining rules)
    if not memory.get("location_preferences"):
        # Include examples only when needed (vague queries)
        examples = [
            {"role": "user", "content": "What universities should I join?"},
            {"role": "assistant", "content": "I'd love to help! To give accurate recommendations, I need to know:\n1. What field? (CS, Engineering, etc)\n2. What region? (Gilgit, Skardu, etc)\n3. Budget constraints?\nLet me search once I have these details."},

            {"role": "user", "content": "Tell me about UNICORN University"},
            {"role": "assistant", "content": "I don't have UNICORN University in our database. Let me search online for you... [uses brave_search]"}
        ]
        return [system_msg] + examples
    else:
        # Already have context, just system prompt
        return [system_msg]

# Usage
prompt_messages = get_counselor_prompt(json.dumps(memory))
# First message: 600 tokens (system + examples)
# Later messages: 80 tokens (system only)
```

**Why this combo:**
- ✅ First message stays under 1000 tokens (ample room)
- ✅ Later messages ~200 tokens (very efficient)
- ✅ Examples teach AI correct behavior better than rules
- ✅ Simple to implement
- ✅ No external dependencies

---

## Quick Implementation

```python
# Replace your get_counselor_prompt with this:
def get_counselor_prompt(memory_string: str = "{}") -> dict:
    memory = json.loads(memory_string) if memory_string != "{}" else {}
    has_context = bool(memory.get("location_preferences"))

    if has_context:
        # Lean version for known context
        return {
            "role": "system",
            "content": (
                "You are an AI University Counselor.\n"
                "Use search_universities for facts. Never invent universities.\n"
                f"Student: {memory_string}\n"
                "Be helpful and accurate."
            )
        }
    else:
        # Normal version for first interaction
        return {
            "role": "system",
            "content": (
                "You are an AI University Counselor.\n"
                "Use search_universities for university facts.\n"
                "Never invent institutions or requirements.\n"
                "For vague queries, ask: location, field, budget.\n"
                f"Context: {memory_string}\n"
            )
        }
```

---

## Summary

| Approach | Token Cost | Implementation Time | Recommended |
|----------|-----------|-------------------|-------------|
| Current (compressed) | ~700 tokens | ✅ Done | **Use Now** |
| Conditional prompts | ~200 tokens | 30 min | **Add Soon** |
| Few-shot examples | ~300 tokens | 1 hour | **Add Soon** |
| Dynamic retrieval | ~300 tokens | 3 hours | Later |
| Vector embeddings | ~200 tokens | 5+ hours | Only if 50+ rules |

**My suggestion:** What you have now (compressed ~700 tokens) is solid. Add conditional prompting next to get it down to ~200 tokens for most calls. This gets you the best token efficiency with minimal code changes.

Would you like me to implement the conditional prompting version?
