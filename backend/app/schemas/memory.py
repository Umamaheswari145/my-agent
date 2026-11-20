from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    kind: str = Field(default="fact", max_length=50)


class MemoryUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    kind: str | None = Field(default=None, max_length=50)


class MemoryResponse(ORMModel):
    id: UUID
    content: str
    kind: str
    created_at: datetime
    updated_at: datetime
