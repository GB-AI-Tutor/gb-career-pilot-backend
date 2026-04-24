from src.services.coversation_history import get_counselor_prompt


def test_counselor_prompt_includes_structure_rules():
    prompt = get_counselor_prompt("{}")
    content = prompt["content"]

    assert "RESPONSE FORMAT (MANDATORY):" in content
    assert "**Quick Answer**" in content
    assert "**Top Options**" in content
    assert "**What You Should Do Next**" in content
    assert "**Question for You**" in content


def test_counselor_prompt_preserves_database_grounding_rules():
    prompt = get_counselor_prompt("{}")
    content = prompt["content"]

    assert "Based on our university database" in content
    assert "NEVER make up universities" in content
