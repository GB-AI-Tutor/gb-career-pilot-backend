from unittest.mock import MagicMock, patch

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

    with patch("src.api.v1.endpoints.ai_endpoints.client") as mock_groq:
        # Use side_effect to handle multiple calls
        mock_groq.chat.completions.create.return_value = mock_response1

        response = client.post(
            "/api/v1/groq/chat", json={"messages": [{"role": "user", "content": "Hi!"}]}
        )

        # Verify the response
        assert response.status_code == 200
        data = response.json()

        # Check that content is returned
        assert "content" in data
        assert data["content"] == "Hi there! How can I help you find universities?"

        # Get the arguments used in the call
        args, kwargs = mock_groq.chat.completions.create.call_args

        # 'messages' was passed as a keyword argument
        sent_messages = kwargs["messages"]

        first_message = sent_messages[0]
        second_message = sent_messages[1]

        # Verify system prompt and user message were included
        assert first_message["role"] == "system"
        assert second_message["role"] == "user"
        assert second_message["content"] == "Hi!"
