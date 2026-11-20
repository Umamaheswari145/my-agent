from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class PreferenceUpdate(BaseModel):
    response_style: str | None = Field(default=None, max_length=100)
    tone: str | None = Field(default=None, max_length=100)
    verbosity: Literal["concise", "balanced", "detailed"] | None = None
    extra_instructions: str | None = Field(default=None, max_length=4000)
    memory_enabled: bool | None = None


class PreferenceResponse(ORMModel):
    id: int
    response_style: str
    tone: str
    verbosity: str
    extra_instructions: str
    memory_enabled: bool
    updated_at: datetime
