from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from groq import APIConnectionError, RateLimitError

from src.main import app
from src.utils.ai_client import get_basic_completion

client = TestClient(app)


def test_basic_completion_success(mocker):
    mocker_reponse = mocker.MagicMock()
    mocker_reponse.choices[0].message.content = "This is a fake AI answer."

    mocker.patch("src.utils.ai_client.client.chat.completions.create", return_value=mocker_reponse)

    result = get_basic_completion("What is the capital of GB?")

    assert result == "This is a fake AI answer."


def test_basic_completion_rate_limit(mocker):
    # 1. We tell the mock to RAISE a RateLimitError when called
    # (Notice we use side_effect instead of return_value)
    mocker.patch(
        "src.utils.ai_client.client.chat.completions.create",
        side_effect=RateLimitError("Rate limit exceeded", response=mocker.MagicMock(), body=None),
    )

    # 2. We tell pytest: "Hey, expect an HTTPException to happen right here!"
    with pytest.raises(HTTPException) as exception_info:
        # 3. We call our function
        get_basic_completion("What is the capital of GB?")

    # 4. We can even assert that the correct status code was sent back to the student
    assert exception_info.value.status_code == 429


def test_basic_completion_connection_error(mocker):
    # 1. We change the side_effect to our new error
    mocker.patch(
        "src.utils.ai_client.client.chat.completions.create",
        side_effect=APIConnectionError(message="Connection failed", request=mocker.MagicMock()),
    )

    # 2. We still expect an HTTPException to be raised
    with pytest.raises(HTTPException) as exception_info:
        get_basic_completion("What is the capital of GB?")

    # 3. We verify the status code matches your ai_client.py logic
    assert exception_info.value.status_code == 503


def test_chat_stream():
    # Create mock response for the first non-streaming call
    mock_response1 = MagicMock()
    mock_response1.choices = [MagicMock()]
    mock_response1.choices[0].message.tool_calls = []  # No tool calls
    mock_response1.choices[0].message.content = "Hi there! How can I help you find universities?"

    # Mock streaming chunks for the second (stream=True) call
    stream_chunk = MagicMock()
    stream_chunk.choices = [MagicMock()]
    stream_chunk.choices[0].delta.content = "Hi there! How can I help you find universities?"

    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[])
    )
    mock_db.table.return_value.insert.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[{"id": "conv-test-1"}])
    )

    async def override_get_current_user():
        return {"id": "user-123", "email": "student2@gmail.com"}

    async def override_rate_limiter():
        return True

    from src.api.v1.deps import get_current_user, rate_limiter

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[rate_limiter] = override_rate_limiter

    try:
        with (
            patch("src.api.v1.endpoints.ai_endpoints.client") as mock_groq,
            patch(
                "src.api.v1.endpoints.ai_endpoints.get_supabase_admin_client",
                new=AsyncMock(return_value=mock_db),
            ),
            patch(
                "src.api.v1.endpoints.ai_endpoints.convertion_history",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "src.api.v1.endpoints.ai_endpoints.extract_and_update_memory",
                new=AsyncMock(return_value=None),
            ),
        ):
            # Use side_effect to handle multiple calls
            mock_groq.chat.completions.create.side_effect = [mock_response1, [stream_chunk]]

            response = client.post(
                "/api/v1/groq/chat", json={"messages": [{"role": "user", "content": "Hi!"}]}
            )

            # Verify the response
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            assert "data: Hi there! How can I help you find universities?" in response.text
            assert "[DONE_CONV_ID:" in response.text

            # Get the arguments used in the call
            _, kwargs = mock_groq.chat.completions.create.call_args_list[0]

            # 'messages' was passed as a keyword argument
            sent_messages = kwargs["messages"]
            assert len(sent_messages) >= 1
            assert sent_messages[0]["role"] == "system"
    finally:
        app.dependency_overrides.clear()
