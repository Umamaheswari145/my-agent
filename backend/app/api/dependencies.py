from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.llm.base import LLMProvider
from app.llm.factory import create_provider
from app.models import User
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.memory_service import MemoryService
from app.services.model_config_service import ModelConfigService
from app.services.preference_service import PreferenceService
from app.services.user_service import UserService


def get_current_user(db: Session = Depends(get_db)) -> User:
    return UserService().get_or_create_default(db)


def get_conversation_service() -> ConversationService:
    return ConversationService()


def get_memory_service() -> MemoryService:
    return MemoryService()


def get_preference_service() -> PreferenceService:
    return PreferenceService()


def get_model_config_service() -> ModelConfigService:
    return ModelConfigService()


def get_document_service() -> DocumentService:
    return DocumentService(settings)


def get_optional_provider(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LLMProvider | None:
    config = ModelConfigService().get_or_create(db, user, settings)
    llm_config = ModelConfigService.llm_config(config, settings)
    if not llm_config.api_key:
        return None
    return create_provider(llm_config)
