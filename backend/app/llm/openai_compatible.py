import json
import logging
from collections.abc import AsyncIterator, Sequence

from openai import AsyncOpenAI
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
)

from app.llm.base import (
    ChatMessage,
    ChatResponse,
    LLMConfig,
    LLMProvider,
    StreamDelta,
    parse_json_object,
    ToolCall,
    ToolCallDelta,
    ToolDefinition,
)
from app.llm.errors import (
    ProviderAuthError,
    ProviderModelError,
    ProviderNotConfiguredError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


def _to_api_messages(messages: Sequence[ChatMessage]) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for message in messages:
        item: dict[str, object] = {"role": message.role, "content": message.content}
        if message.tool_calls:
            item["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments),
                    },
                }
                for call in message.tool_calls
            ]
        if message.tool_call_id:
            item["tool_call_id"] = message.tool_call_id
        if message.name:
            item["name"] = message.name
        payload.append(item)
    return payload


def _to_api_tools(tools: Sequence[ToolDefinition]) -> list[dict[str, object]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in tools
    ]


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        if not config.api_key:
            raise ProviderNotConfiguredError(
                "LLM_API_KEY is not configured. Add it to backend/.env to enable AI responses."
            )
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            max_retries=1,
        )

    async def achat(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] = (),
    ) -> ChatResponse:
        try:
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=_to_api_messages(messages),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                tools=_to_api_tools(tools) if tools else None,
            )
        except Exception as exc:
            _raise_provider_error(exc)

        choice = response.choices[0] if response.choices else None
        if choice is None:
            raise ProviderResponseError("The provider returned an empty response.")

        tool_calls: tuple[ToolCall, ...] = ()
        if choice.message.tool_calls:
            tool_calls = tuple(
                ToolCall(
                    id=call.id,
                    name=call.function.name,
                    arguments=parse_json_object(call.function.arguments),
                )
                for call in choice.message.tool_calls
            )
        return ChatResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
        )

    async def astream(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] = (),
    ) -> AsyncIterator[StreamDelta]:
        try:
            stream = await self._client.chat.completions.create(
                model=self.config.model,
                messages=_to_api_messages(messages),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                tools=_to_api_tools(tools) if tools else None,
                stream=True,
            )
            async for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                if choice is None:
                    continue
                delta = choice.delta
                tool_deltas: tuple[ToolCallDelta, ...] = ()
                if delta.tool_calls:
                    tool_deltas = tuple(
                        ToolCallDelta(
                            index=call.index,
                            id=call.id,
                            name=call.function.name if call.function else None,
                            arguments_fragment=(
                                call.function.arguments if call.function and call.function.arguments else ""
                            ),
                        )
                        for call in delta.tool_calls
                    )
                yield StreamDelta(
                    text=delta.content or "",
                    tool_calls=tool_deltas,
                    finish_reason=choice.finish_reason,
                )
        except Exception as exc:
            _raise_provider_error(exc)

    async def aembed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.config.embedding_model:
            raise ProviderNotConfiguredError("Embeddings are disabled; keyword search will be used.")
        try:
            response = await self._client.embeddings.create(
                model=self.config.embedding_model,
                input=list(texts),
            )
        except Exception as exc:
            _raise_provider_error(exc)
        return [list(item.embedding) for item in sorted(response.data, key=lambda item: item.index)]


def _is_quota_error(exc: Exception) -> bool:
    body = getattr(exc, "body", None)
    detail = (json.dumps(body) if body is not None else str(exc)).lower()
    return any(
        marker in detail
        for marker in (
            "insufficient_quota",
            "credit_balance_exhausted",
            "no credits remaining",
            "billing hard limit",
        )
    )


def _raise_provider_error(exc: Exception) -> None:
    logger.warning("LLM provider error: %s: %s", type(exc).__name__, exc)
    if isinstance(exc, AuthenticationError):
        raise ProviderAuthError(
            "The LLM provider rejected the API key. Check LLM_API_KEY.",
        ) from exc
    if isinstance(exc, RateLimitError):
        if _is_quota_error(exc):
            raise ProviderQuotaError(
                "Your LLM provider account has no credits remaining. Add credits or switch providers.",
            ) from exc
        raise ProviderRateLimitError(
            "The LLM provider is rate limiting requests. Try again shortly.",
        ) from exc
    if isinstance(exc, APITimeoutError):
        raise ProviderTimeoutError(
            "The LLM provider took too long to respond. Try again.",
        ) from exc
    if isinstance(exc, APIConnectionError):
        raise ProviderUnavailableError(
            "The LLM provider is unreachable. Check LLM_BASE_URL and your connection.",
        ) from exc
    if isinstance(exc, (NotFoundError, BadRequestError)):
        detail = str(exc).lower()
        if "model" in detail or "not found" in detail:
            raise ProviderModelError(
                "The configured LLM model is unavailable. Check LLM_MODEL.",
            ) from exc
        raise ProviderResponseError("The LLM provider rejected the request.") from exc
    if isinstance(exc, APIStatusError):
        if exc.status_code == 401 or exc.status_code == 403:
            raise ProviderAuthError(
                "The LLM provider rejected the credentials."
            ) from exc
        if exc.status_code == 429:
            if _is_quota_error(exc):
                raise ProviderQuotaError(
                    "Your LLM provider account has no credits remaining. Add credits or switch providers.",
                ) from exc
            raise ProviderRateLimitError(
                "The LLM provider is rate limiting requests."
            ) from exc
        raise ProviderUnavailableError(
            "The LLM provider returned an unexpected error."
        ) from exc
    if isinstance(exc, APIError):
        raise ProviderUnavailableError("The LLM provider failed.") from exc
    if isinstance(exc, TimeoutError):
        raise ProviderTimeoutError("The LLM request timed out.") from exc
    raise ProviderResponseError("The LLM provider returned an invalid response.") from exc
