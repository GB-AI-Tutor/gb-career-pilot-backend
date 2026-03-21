from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTENT = "assistent"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1, description="The text content of the message")


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        ..., min_length=1, description=" The full conversation history, include the new message"
    )
    conversation_id: UUID | None = Field(default=None)
