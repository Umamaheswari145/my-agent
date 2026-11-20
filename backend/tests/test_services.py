from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Memory
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.services.model_config_service import ModelConfigService
from app.services.preference_service import PreferenceService
from app.models import User
from tests.fakes import FakeProvider


def _conversation_with_message(db: Session, user: User, service: ConversationService):
    conversation = service.create(db, user)
    service.add_message(db, conversation, role="user", content="Hello there")
    service.add_message(db, conversation, role="assistant", content="Hi!")
    return conversation


def test_conversation_create_get_and_scope(db_session: Session, test_user: User) -> None:
    service = ConversationService()
    conversation = service.create(db_session, test_user, "My title")

    assert isinstance(conversation.id, UUID)
    assert service.get(db_session, test_user, conversation.id).title == "My title"
    with pytest.raises(AppError) as exc:
        service.get(db_session, test_user, UUID(int=999))
    assert exc.value.status_code == 404


def test_conversation_rename_and_delete(db_session: Session, test_user: User) -> None:
    service = ConversationService()
    conversation = service.create(db_session, test_user)
    renamed = service.rename(db_session, conversation, "Renamed")
    assert renamed.title == "Renamed"

    service.delete(db_session, renamed)
    with pytest.raises(AppError):
        service.get(db_session, test_user, conversation.id)


def test_conversation_message_order_and_title(db_session: Session, test_user: User) -> None:
    service = ConversationService()
    conversation = service.create(db_session, test_user)
    service.add_message(db_session, conversation, role="user", content="  First   question  ")
    service.add_message(db_session, conversation, role="assistant", content="Answer")

    messages, total = service.messages(db_session, conversation, 10, 0)
    assert total == 2
    assert [message.role for message in messages] == ["user", "assistant"]

    title = service.set_title_from_message(db_session, conversation, "# How do I use pgvector?")
    assert title == "How do I use pgvector?"
    assert service.get(db_session, test_user, conversation.id).title == title


def test_conversation_pagination_and_search(db_session: Session, test_user: User) -> None:
    service = ConversationService()
    for index in range(3):
        service.create(db_session, test_user, f"chat {index}")
    items, total = service.list(db_session, test_user, 2, 0, query="chat")
    assert total == 3
    assert len(items) == 2
    _, filtered_total = service.list(db_session, test_user, 10, 0, query="missing")
    assert filtered_total == 0


def test_message_update_error_and_recent(db_session: Session, test_user: User) -> None:
    service = ConversationService()
    conversation = _conversation_with_message(db_session, test_user, service)
    assistant = service.add_message(db_session, conversation, role="assistant", content="draft")
    updated = service.update_message(db_session, assistant, "final answer")
    assert updated.content == "final answer"

    failed = service.mark_message_error(db_session, assistant, "failed answer")
    assert failed.is_error is True
    recent = service.recent_messages(db_session, conversation, 2)
    assert len(recent) == 2


@pytest.mark.asyncio
async def test_memory_create_deduplicates_and_updates(
    db_session: Session, test_user: User
) -> None:
    service = MemoryService()
    provider = FakeProvider()
    first = await service.create(
        db_session, test_user, content="I prefer   concise answers", kind="preference", provider=provider
    )
    second = await service.create(
        db_session, test_user, content="I prefer concise answers", kind="preference", provider=provider
    )
    assert first.id == second.id
    assert second.embedding_json is not None

    updated = await service.update(
        db_session, first, content="I prefer detailed answers", provider=provider
    )
    assert updated.content == "I prefer detailed answers"
    assert len(provider.embed_calls) >= 2


@pytest.mark.asyncio
async def test_memory_extraction_ignores_sensitive_data(
    db_session: Session, test_user: User
) -> None:
    service = MemoryService()
    extracted = await service.extract_from_text(
        db_session,
        test_user,
        "My name is Ada. My api key is super-secret-value.",
    )
    assert len(extracted) == 1
    assert "Ada" in extracted[0].content


@pytest.mark.asyncio
async def test_memory_retrieval_keyword_and_semantic(
    db_session: Session, test_user: User
) -> None:
    service = MemoryService()
    await service.create(db_session, test_user, content="I use Python every day", kind="preference")
    await service.create(db_session, test_user, content="I am learning SQL", kind="fact")

    keyword = await service.retrieve(db_session, test_user, "Python", 2)
    assert keyword and "Python" in keyword[0].content

    provider = FakeProvider()
    semantic = await service.retrieve(db_session, test_user, "python", 2, provider)
    assert semantic


def test_memory_list_update_delete(db_session: Session, test_user: User) -> None:
    service = MemoryService()
    memory = Memory(
        user_id=test_user.id,
        content="temporary",
        content_hash="hash",
        kind="fact",
    )
    db_session.add(memory)
    db_session.commit()
    items, total = service.list(db_session, test_user, 10, 0)
    assert total == 1
    assert service.get(db_session, test_user, memory.id).content == "temporary"
    service.delete(db_session, memory)
    assert service.list(db_session, test_user, 10, 0)[1] == 0


def test_preferences_and_model_config(db_session: Session, test_user: User) -> None:
    from app.core.config import settings
    from app.schemas.model_config import AIModelConfigUpdate
    from app.schemas.preference import PreferenceUpdate

    preferences = PreferenceService().get_or_create(db_session, test_user)
    updated = PreferenceService().update(
        db_session, preferences, PreferenceUpdate(verbosity="concise", extra_instructions="Be brief")
    )
    instructions = PreferenceService().instructions(updated)
    assert "concise" in instructions and "Be brief" in instructions

    configs = ModelConfigService()
    config = configs.get_or_create(db_session, test_user, settings)
    changed = configs.update(
        db_session, config, AIModelConfigUpdate(model="test-model", temperature=0.2)
    )
    llm_config = configs.llm_config(changed, settings)
    assert llm_config.model == "test-model"
    assert llm_config.temperature == 0.2
