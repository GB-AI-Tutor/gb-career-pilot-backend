from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTENT = "assistent"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str = Field(
        ..., min_length=1, max_length=2000, description="The text content of the message"
    )

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        # Strip invisible whitespace from the start and end
        clean_text = v.strip()
        if not clean_text:
            raise ValueError("Message cannot be empty or just spaces.")
        return clean_text


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ..., min_length=1, description=" The full conversation history, include the new message"
    )
    conversation_id: UUID | None = Field(default=None)
