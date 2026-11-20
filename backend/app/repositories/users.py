from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

    def get_or_create(self, db: Session, email: str, display_name: str) -> User:
        existing = self.get_by_email(db, email)
        if existing is not None:
            return existing

        user = User(email=email, display_name=display_name)
        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = self.get_by_email(db, email)
            if existing is None:
                raise
            return existing

        db.refresh(user)
        return user
