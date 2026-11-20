from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Message


class MessageRepository:
    def create(
        self,
        db: Session,
        *,
        conversation_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
        tool_name: str | None = None,
        tool_calls: dict | None = None,
        is_error: bool = False,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_calls=tool_calls,
            is_error=is_error,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def list(
        self, db: Session, conversation_id: UUID, limit: int, offset: int
    ) -> tuple[Sequence[Message], int]:
        from sqlalchemy import func

        total = db.scalar(
            select(func.count()).select_from(Message).where(
                Message.conversation_id == conversation_id
            )
        ) or 0
        items = db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .limit(limit)
            .offset(offset)
        ).all()
        return items, total

    def recent(
        self, db: Session, conversation_id: UUID, limit: int
    ) -> Sequence[Message]:
        recent_ids = (
            select(Message.id)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
            .subquery()
        )
        return db.scalars(
            select(Message)
            .join(recent_ids, Message.id == recent_ids.c.id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        ).all()

    def update_content(self, db: Session, message: Message, content: str) -> Message:
        message.content = content
        message.is_error = False
        db.commit()
        db.refresh(message)
        return message

    def mark_error(self, db: Session, message: Message, content: str) -> Message:
        message.content = content
        message.is_error = True
        db.commit()
        db.refresh(message)
        return message

    def delete_tail(self, db: Session, conversation_id: UUID, from_id: UUID) -> None:
        ordered = list(
            db.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc(), Message.id.asc())
            )
        )
        target_index = next((i for i, item in enumerate(ordered) if item.id == from_id), None)
        if target_index is None:
            return
        for message in ordered[target_index:]:
            db.delete(message)
        db.commit()
