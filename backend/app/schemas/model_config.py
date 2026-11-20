from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AIModelConfigUpdate(BaseModel):
    model: str | None = Field(default=None, max_length=200)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=32000)
    system_prompt: str | None = Field(default=None, max_length=12000)
    use_tools: bool | None = None


class AIModelConfigResponse(ORMModel):
    id: int
    provider: str
    model: str
    base_url: str
    temperature: float
    max_tokens: int
    system_prompt: str
    use_tools: bool
    updated_at: datetime
