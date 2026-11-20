from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DocumentResponse(ORMModel):
    id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: str
    chunk_count: int
    error_message: str | None
    created_at: datetime


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=20)


class DocumentSearchResult(BaseModel):
    document_id: UUID
    filename: str
    chunk_index: int
    content: str
    score: float
