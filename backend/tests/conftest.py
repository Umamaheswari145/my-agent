from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_user, get_optional_provider
from app.core.config import settings
from app.core.security import require_access_token
from app.database.session import get_db
from app.models import Base, User
from app.services.user_service import UserService


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    if settings.TEST_DATABASE_URL:
        engine = create_engine(settings.TEST_DATABASE_URL, pool_pre_ping=True, future=True)
    else:
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def test_user(db_session: Session) -> User:
    return UserService().get_or_create_default(db_session)


@pytest.fixture()
def client(db_session: Session, test_user: User) -> Generator[TestClient, None, None]:
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[require_access_token] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_optional_provider] = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
