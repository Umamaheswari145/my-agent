from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.llm.base import LLMConfig
from app.models import AIModelConfig, User
from app.schemas.model_config import AIModelConfigUpdate


class ModelConfigService:
    def get_or_create(self, db: Session, user: User, settings: Settings) -> AIModelConfig:
        config = db.scalar(select(AIModelConfig).where(AIModelConfig.user_id == user.id))
        if config is not None:
            user.model_config = config
            return config
        config = AIModelConfig(
            user_id=user.id,
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            system_prompt=settings.SYSTEM_PROMPT,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        user.model_config = config
        return config

    def update(
        self, db: Session, config: AIModelConfig, changes: AIModelConfigUpdate
    ) -> AIModelConfig:
        for field, value in changes.model_dump(exclude_unset=True).items():
            setattr(config, field, value)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def llm_config(config: AIModelConfig, settings: Settings) -> LLMConfig:
        api_key = settings.LLM_API_KEY.get_secret_value()
        return LLMConfig(
            api_key=api_key,
            model=config.model or settings.LLM_MODEL,
            base_url=config.base_url or settings.LLM_BASE_URL,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            embedding_model=settings.LLM_EMBEDDING_MODEL,
        )
