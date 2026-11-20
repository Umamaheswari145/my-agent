from app.core.config import Settings
from app.llm.base import LLMConfig, LLMProvider
from app.llm.openai_compatible import OpenAICompatibleProvider


def build_llm_config(settings: Settings) -> LLMConfig:
    return LLMConfig(
        api_key=settings.LLM_API_KEY.get_secret_value(),
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        embedding_model=settings.LLM_EMBEDDING_MODEL,
    )


def create_provider(config: LLMConfig) -> LLMProvider:
    return OpenAICompatibleProvider(config)
