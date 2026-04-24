from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class MessageRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: MessageRole = MessageRole.USER
    content: str = Field(
        ..., min_length=1, max_length=2000, description="The text content of the message"
    )
    tool_call_id: str | None = Field(default=None)

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        # Strip invisible whitespace from the start and end
        clean_text = v.strip()
        if not clean_text:
            raise ValueError("Message cannot be empty or just spaces.")
        return clean_text

    @field_validator("tool_call_id")
    @classmethod
    def sanitize_tool_call_id(cls, v: str | None) -> str | None:
        if v is None:
            return None

        clean_id = v.strip()
        return clean_id or None

    @model_validator(mode="after")
    def validate_tool_message_fields(self) -> "ChatMessage":
        if self.role == MessageRole.TOOL and not self.tool_call_id:
            raise ValueError("tool_call_id is required when role is 'tool'")
        return self


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ..., min_length=1, description=" The full conversation history, include the new message"
    )
    conversation_id: UUID | None = Field(default=None)

    @field_validator("messages", mode="before")
    @classmethod
    def normalize_messages(cls, value):
        if not isinstance(value, list):
            raise ValueError("messages must be a list")

        normalized = []
        for index, message in enumerate(value):
            if isinstance(message, str):
                normalized.append({"role": "user", "content": message})
                continue

            if isinstance(message, dict):
                message_copy = message.copy()
                if not message_copy.get("role"):
                    message_copy["role"] = "user"
                if "content" not in message_copy:
                    raise ValueError(
                        f"Message at index {index} is missing required 'content' field"
                    )
                normalized.append(message_copy)
                continue

            raise ValueError(
                f"Message at index {index} must be an object with 'role' and 'content'"
            )

        return normalized
