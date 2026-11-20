from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ConversationResponse(ORMModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(ORMModel):
    id: UUID
    conversation_id: UUID
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    created_at: datetime
    tool_name: str | None = None
    is_error: bool = False


class ChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20000)
    conversation_id: UUID | None = None
    regenerate_of: UUID | None = None
    use_web_search: bool = False


class ChatStartedEvent(BaseModel):
    type: Literal["started"] = "started"
    conversation_id: UUID
    user_message_id: UUID
    assistant_message_id: UUID
    title: str


class ChatDoneEvent(BaseModel):
    type: Literal["done"] = "done"
    message: MessageResponse


class ChatDeltaEvent(BaseModel):
    type: Literal["delta"] = "delta"
    content: str


class ChatErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    code: str
    message: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    title: str
    message: MessageResponse
    user_message_id: UUID
