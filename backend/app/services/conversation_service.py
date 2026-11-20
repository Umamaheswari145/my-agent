import re
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import USER_ROLE
from app.core.errors import AppError
from app.models import Conversation, Message, User
from app.repositories.conversations import ConversationRepository
from app.repositories.messages import MessageRepository


class ConversationService:
    def __init__(self) -> None:
        self._conversations = ConversationRepository()
        self._messages = MessageRepository()

    def create(self, db: Session, user: User, title: str | None = None) -> Conversation:
        return self._conversations.create(db, user.id, title or "New chat")

    def get(self, db: Session, user: User, conversation_id: UUID) -> Conversation:
        conversation = self._conversations.get(db, user.id, conversation_id)
        if conversation is None:
            raise AppError("Conversation not found.", status_code=404, error_code="not_found")
        return conversation

    def list(
        self,
        db: Session,
        user: User,
        limit: int,
        offset: int,
        query: str | None = None,
    ) -> tuple[list[Conversation], int]:
        return self._conversations.list(db, user.id, limit, offset, query)

    def rename(self, db: Session, conversation: Conversation, title: str) -> Conversation:
        return self._conversations.rename(db, conversation, title)

    def delete(self, db: Session, conversation: Conversation) -> None:
        self._conversations.delete(db, conversation)

    def add_message(
        self,
        db: Session,
        conversation: Conversation,
        *,
        role: str,
        content: str,
        **kwargs: object,
    ) -> Message:
        message = self._messages.create(
            db,
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            role=role,
            content=content,
            **kwargs,
        )
        self._conversations.touch(db, conversation)
        return message

    def update_message(self, db: Session, message: Message, content: str) -> Message:
        return self._messages.update_content(db, message, content)

    def mark_message_error(self, db: Session, message: Message, content: str) -> Message:
        return self._messages.mark_error(db, message, content)

    def messages(
        self, db: Session, conversation: Conversation, limit: int, offset: int
    ) -> tuple[Sequence[Message], int]:
        return self._messages.list(db, conversation.id, limit, offset)

    def recent_messages(
        self, db: Session, conversation: Conversation, limit: int
    ) -> Sequence[Message]:
        return self._messages.recent(db, conversation.id, limit)

    def set_title_from_message(
        self, db: Session, conversation: Conversation, content: str
    ) -> str:
        title = self._title_from_text(content)
        self._conversations.set_title_if_default(db, conversation, title)
        return title

    @staticmethod
    def _title_from_text(content: str) -> str:
        cleaned = re.sub(r"\s+", " ", content).strip()
        cleaned = re.sub(r"^[#>*`-]+\s*", "", cleaned)
        if not cleaned:
            return "New chat"
        if len(cleaned) > 60:
            return cleaned[:57].rstrip() + "..."
        return cleaned

    def last_user_message(
        self, db: Session, conversation: Conversation
    ) -> Message | None:
        from sqlalchemy import select

        return db.scalar(
            select(Message)
            .where(
                Message.conversation_id == conversation.id,
                Message.role == USER_ROLE,
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
        )
