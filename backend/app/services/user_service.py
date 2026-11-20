from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User
from app.repositories.users import UserRepository


class UserService:
    def __init__(self) -> None:
        self._repository = UserRepository()

    def get_or_create_default(self, db: Session) -> User:
        return self._repository.get_or_create(
            db,
            email=settings.DEFAULT_USER_EMAIL,
            display_name=settings.DEFAULT_USER_NAME,
        )
