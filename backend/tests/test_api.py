from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_provider
from app.core.config import settings
from app.database.session import get_db
from app.llm.base import ChatResponse, StreamDelta
from app.llm.errors import ProviderRateLimitError
from app.main import app
from app.models import User
from tests.fakes import FakeProvider


def test_auth_required(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "APP_ACCESS_TOKEN", SecretStr("test-token"))
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as client:
            assert client.get("/api/conversations").status_code == 401
            assert (
                client.get("/api/conversations", headers={"X-API-Key": "test-token"}).status_code
                == 200
            )
    finally:
        app.dependency_overrides.clear()


def test_conversation_api_crud(client: TestClient) -> None:
    created = client.post("/api/conversations", json={"title": "API test"})
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    listed = client.get("/api/conversations?limit=10&offset=0")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    renamed = client.patch(f"/api/conversations/{conversation_id}", json={"title": "Renamed"})
    assert renamed.json()["title"] == "Renamed"

    fetched = client.get(f"/api/conversations/{conversation_id}")
    assert fetched.status_code == 200

    messages = client.get(f"/api/conversations/{conversation_id}/messages")
    assert messages.json() == {"items": [], "total": 0, "limit": 100, "offset": 0}

    assert client.delete(f"/api/conversations/{conversation_id}").status_code == 204
    assert client.get(f"/api/conversations/{conversation_id}").status_code == 404


def test_conversation_not_found_and_validation(client: TestClient) -> None:
    assert client.get(f"/api/conversations/{UUID(int=42)}").status_code == 404
    assert client.patch("/api/conversations/not-a-uuid", json={"title": "x"}).status_code == 400
    assert client.post("/api/conversations", json={"title": ""}).status_code == 422


def test_preferences_and_model_config_api(client: TestClient) -> None:
    preferences = client.get("/api/preferences").json()
    assert preferences["verbosity"] == "balanced"

    updated = client.patch("/api/preferences", json={"verbosity": "concise"})
    assert updated.json()["verbosity"] == "concise"

    config = client.get("/api/model-config").json()
    assert config["model"]
    patched = client.patch("/api/model-config", json={"temperature": 0.3, "model": "custom"})
    assert patched.json()["temperature"] == 0.3
    assert patched.json()["model"] == "custom"


def test_memory_api_crud(client: TestClient) -> None:
    created = client.post(
        "/api/memories", json={"content": "I prefer concise answers", "kind": "preference"}
    )
    assert created.status_code == 201
    memory_id = created.json()["id"]

    listed = client.get("/api/memories").json()
    assert listed["total"] == 1

    updated = client.patch(
        f"/api/memories/{memory_id}", json={"content": "I prefer detailed answers"}
    )
    assert updated.json()["content"] == "I prefer detailed answers"

    assert client.delete(f"/api/memories/{memory_id}").status_code == 204
    assert client.get("/api/memories").json()["total"] == 0


def test_document_api_upload_search_delete(client: TestClient) -> None:
    uploaded = client.post(
        "/api/documents",
        files={"file": ("notes.md", b"# Notes\nPython is a programming language. SQL stores data.", "text/markdown")},
    )
    assert uploaded.status_code == 201
    body = uploaded.json()
    assert body["status"] == "ready"
    assert body["chunk_count"] >= 1
    document_id = body["id"]

    results = client.post("/api/documents/search", json={"query": "Python", "limit": 3})
    assert results.status_code == 200
    assert results.json() and "Python" in results.json()[0]["content"]

    assert client.get("/api/documents").json()["total"] == 1
    assert client.delete(f"/api/documents/{document_id}").status_code == 204
    assert client.get("/api/documents").json()["total"] == 0


def test_document_upload_rejects_invalid_extension(client: TestClient) -> None:
    response = client.post(
        "/api/documents", files={"file": ("virus.exe", b"data", "application/octet-stream")}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_file"


def test_chat_without_provider_returns_503(client: TestClient) -> None:
    response = client.post("/api/chat", json={"content": "hello"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "llm_not_configured"


def test_chat_persists_messages(client: TestClient) -> None:
    provider = FakeProvider([ChatResponse(content="**Bold** answer", finish_reason="stop")])
    app.dependency_overrides[get_optional_provider] = lambda: provider

    response = client.post("/api/chat", json={"content": "Explain something"})
    assert response.status_code == 200
    body = response.json()
    assert body["message"]["content"] == "**Bold** answer"
    assert body["title"] == "Explain something"

    messages = client.get(f"/api/conversations/{body['conversation_id']}/messages").json()
    assert [item["role"] for item in messages["items"]] == ["user", "assistant"]


def test_chat_stream_sse(client: TestClient) -> None:
    provider = FakeProvider(
        stream=[
            StreamDelta(text="Hello "),
            StreamDelta(text="world", finish_reason="stop"),
        ]
    )
    app.dependency_overrides[get_optional_provider] = lambda: provider

    response = client.post(
        "/api/chat/stream", json={"content": "stream please", "use_web_search": False}
    )
    assert response.status_code == 200
    assert 'event: started' in response.text
    assert 'event: delta' in response.text
    assert 'event: done' in response.text
    assert "Hello world" in response.text


def test_chat_stream_error_event(client: TestClient) -> None:
    class FailingProvider(FakeProvider):
        async def astream(self, messages, tools=()):  # type: ignore[no-untyped-def]
            raise ProviderRateLimitError("rate limited")
            yield  # pragma: no cover

    app.dependency_overrides[get_optional_provider] = lambda: FailingProvider()

    response = client.post("/api/chat/stream", json={"content": "fail"})
    assert "event: error" in response.text
    assert "rate limited" in response.text


def test_regenerate_replaces_last_answer(client: TestClient) -> None:
    provider = FakeProvider(
        [
            ChatResponse(content="First answer", finish_reason="stop"),
            ChatResponse(content="Second answer", finish_reason="stop"),
        ]
    )
    app.dependency_overrides[get_optional_provider] = lambda: provider

    first = client.post("/api/chat", json={"content": "Question"}).json()
    second = client.post(
        "/api/chat",
        json={
            "content": "Question",
            "conversation_id": first["conversation_id"],
            "regenerate_of": first["message"]["id"],
        },
    )
    assert second.status_code == 200
    assert second.json()["message"]["content"] == "Second answer"

    messages = client.get(f"/api/conversations/{first['conversation_id']}/messages").json()
    assert [item["role"] for item in messages["items"]] == ["user", "assistant"]
    assert messages["items"][1]["content"] == "Second answer"


def test_isolation_between_users(db_session: Session, test_user: User) -> None:
    from app.services.conversation_service import ConversationService

    other = User(email="other@example.test", display_name="Other")
    db_session.add(other)
    db_session.commit()
    service = ConversationService()
    conversation = service.create(db_session, other, "other chat")

    with pytest.raises(Exception):
        service.get(db_session, test_user, conversation.id)
