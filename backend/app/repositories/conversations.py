from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.models import Conversation


class ConversationRepository:
    def create(self, db: Session, user_id: UUID, title: str) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def get(self, db: Session, user_id: UUID, conversation_id: UUID) -> Conversation | None:
        return db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

    def list(
        self,
        db: Session,
        user_id: UUID,
        limit: int,
        offset: int,
        query: str | None = None,
    ) -> tuple[list[Conversation], int]:
        filters = [Conversation.user_id == user_id]
        if query:
            filters.append(Conversation.title.ilike(f"%{query}%"))

        total = db.scalar(
            select(func.count()).select_from(Conversation).where(*filters)
        ) or 0
        items = list(
            db.scalars(
                select(Conversation)
                .where(*filters)
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total

    def rename(self, db: Session, conversation: Conversation, title: str) -> Conversation:
        conversation.title = title
        db.commit()
        db.refresh(conversation)
        return conversation

    def touch(self, db: Session, conversation: Conversation) -> None:
        conversation.updated_at = func.now()
        db.commit()

    def delete(self, db: Session, conversation: Conversation) -> None:
        db.execute(delete(Conversation).where(Conversation.id == conversation.id))
        db.commit()

    def set_title_if_default(
        self, db: Session, conversation: Conversation, title: str
    ) -> Conversation:
        if not conversation.title.startswith("New chat"):
            return conversation
        conversation.title = title
        db.execute(
            update(Conversation).where(Conversation.id == conversation.id).values(title=title)
        )
        db.commit()
        db.refresh(conversation)
        return conversation
