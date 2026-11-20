from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/personal_ai_agent"
    TEST_DATABASE_URL: str = ""

    APP_ACCESS_TOKEN: SecretStr = SecretStr("")
    RATE_LIMIT_PER_MINUTE: int = Field(default=120, ge=1)
    FRONTEND_URL: str = "http://localhost:5173"

    LLM_API_KEY: SecretStr = SecretStr("")
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_PROVIDER: str = "openai-compatible"
    LLM_TEMPERATURE: float = Field(default=0.7, ge=0, le=2)
    LLM_MAX_TOKENS: int = Field(default=2048, ge=1)
    LLM_TIMEOUT_SECONDS: float = Field(default=60.0, ge=1)
    LLM_EMBEDDING_MODEL: str = "text-embedding-3-small"
    SYSTEM_PROMPT: str = ""

    WEB_SEARCH_API_KEY: SecretStr = SecretStr("")
    WEB_SEARCH_BASE_URL: str = "https://api.search.brave.com/res/v1/web/search"

    DEFAULT_USER_EMAIL: str = "owner@personal-ai-agent.local"
    DEFAULT_USER_NAME: str = "Owner"
    MAX_CONTEXT_MESSAGES: int = Field(default=20, ge=1)
    MEMORY_TOP_K: int = Field(default=5, ge=1)
    DOCUMENT_TOP_K: int = Field(default=5, ge=1)
    CHUNK_SIZE: int = Field(default=1000, ge=100)
    CHUNK_OVERLAP: int = Field(default=150, ge=0)
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_MB: int = Field(default=10, ge=1)

    @property
    def cors_origins(self) -> list[str]:
        origins = {origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()}
        origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
        return sorted(origins)

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
