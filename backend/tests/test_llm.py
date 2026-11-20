from types import SimpleNamespace

import httpx
import pytest
from openai import AuthenticationError, RateLimitError
from pydantic import SecretStr

from app.core.config import settings
from app.llm.base import ChatMessage, LLMConfig
from app.llm.errors import (
    ProviderAuthError,
    ProviderNotConfiguredError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderResponseError,
)
from app.llm.factory import build_llm_config, create_provider
from app.llm.openai_compatible import OpenAICompatibleProvider, _raise_provider_error


class _Completions:
    def __init__(self, response: object, stream: list[object] | None = None) -> None:
        self.response = response
        self.stream = stream or []

    async def create(self, **kwargs: object) -> object:
        if kwargs.get("stream"):
            async def iterate():
                for item in self.stream:
                    yield item
            return iterate()
        return self.response


class _Embeddings:
    async def create(self, **kwargs: object) -> object:
        return SimpleNamespace(
            data=[SimpleNamespace(index=index, embedding=[0.1, 0.2]) for index, _ in enumerate(kwargs["input"])]
        )


class _FakeClient:
    def __init__(self, response: object, stream: list[object] | None = None) -> None:
        self.chat = SimpleNamespace(completions=_Completions(response, stream))
        self.embeddings = _Embeddings()


def _config() -> LLMConfig:
    return LLMConfig(api_key="test", model="test-model", base_url="https://example.test/v1")


def _response() -> object:
    message = SimpleNamespace(
        content="Hello",
        tool_calls=[
            SimpleNamespace(
                id="call-1",
                function=SimpleNamespace(name="calculator", arguments='{"expression":"1+1"}'),
            )
        ],
    )
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="tool_calls")])


@pytest.mark.asyncio
async def test_provider_chat_and_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.llm.openai_compatible.AsyncOpenAI",
        lambda **kwargs: _FakeClient(_response()),
    )
    provider = OpenAICompatibleProvider(_config())
    response = await provider.achat([ChatMessage(role="user", content="hi")])
    assert response.content == "Hello"
    assert response.tool_calls[0].name == "calculator"
    assert response.tool_calls[0].arguments == {"expression": "1+1"}

    vectors = await provider.aembed(["a", "b"])
    assert vectors == [[0.1, 0.2], [0.1, 0.2]]


@pytest.mark.asyncio
async def test_provider_disabled_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.llm.openai_compatible.AsyncOpenAI",
        lambda **kwargs: _FakeClient(_response()),
    )
    config = LLMConfig(api_key="test", model="test-model", base_url="https://example.test/v1", embedding_model="")
    provider = OpenAICompatibleProvider(config)
    with pytest.raises(ProviderNotConfiguredError):
        await provider.aembed(["a"])


@pytest.mark.asyncio
async def test_provider_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    chunks = [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="Par", tool_calls=None),
                    finish_reason=None,
                )
            ]
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="tial", tool_calls=None),
                    finish_reason="stop",
                )
            ]
        ),
    ]
    monkeypatch.setattr(
        "app.llm.openai_compatible.AsyncOpenAI",
        lambda **kwargs: _FakeClient(_response(), chunks),
    )
    provider = OpenAICompatibleProvider(_config())
    deltas = [delta async for delta in provider.astream([ChatMessage(role="user", content="hi")])]
    assert "".join(delta.text for delta in deltas) == "Partial"
    assert deltas[-1].finish_reason == "stop"


def test_provider_requires_api_key() -> None:
    config = LLMConfig(api_key="", model="x", base_url="https://example.test/v1")
    with pytest.raises(ProviderNotConfiguredError):
        OpenAICompatibleProvider(config)


def test_error_mapping() -> None:
    request = httpx.Request("POST", "https://example.test/v1/chat/completions")
    with pytest.raises(ProviderAuthError):
        _raise_provider_error(
            AuthenticationError("bad key", response=httpx.Response(401, request=request), body=None)
        )
    with pytest.raises(ProviderRateLimitError):
        _raise_provider_error(
            RateLimitError("slow down", response=httpx.Response(429, request=request), body=None)
        )
    with pytest.raises(ProviderQuotaError):
        _raise_provider_error(
            RateLimitError(
                "no credits remaining",
                response=httpx.Response(429, request=request),
                body={"error": {"code": "insufficient_quota"}},
            )
        )
    with pytest.raises(ProviderResponseError):
        _raise_provider_error(ValueError("unknown"))


def test_factory_uses_environment_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_API_KEY", SecretStr("test-key"))
    config = build_llm_config(settings)
    provider = create_provider(config)
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.config.model == settings.LLM_MODEL
