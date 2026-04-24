import pytest
from pydantic import ValidationError

from src.schemas.ai_schemas import ChatRequest, MessageRole


def test_chat_request_accepts_tool_message_with_tool_call_id():
    payload = {
        "messages": [
            {"role": "user", "content": "Find universities in Islamabad"},
            {"role": "assistant", "content": "Calling search tool"},
            {
                "role": "tool",
                "tool_call_id": "call_abc123",
                "content": '{"universities": []}',
            },
        ]
    }

    req = ChatRequest(**payload)

    assert req.messages[2].role == MessageRole.TOOL
    assert req.messages[2].tool_call_id == "call_abc123"


def test_chat_request_rejects_tool_message_without_tool_call_id():
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(messages=[{"role": "tool", "content": "{}"}])

    assert "tool_call_id is required" in str(exc_info.value)


def test_chat_request_normalizes_string_message_to_user_role():
    req = ChatRequest(messages=["hello"])

    assert req.messages[0].role == MessageRole.USER
    assert req.messages[0].content == "hello"
