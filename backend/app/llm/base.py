import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    model: str
    base_url: str
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_seconds: float = 60.0
    embedding_model: str = "text-embedding-3-small"


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
    name: str | None = None


@dataclass(frozen=True)
class ChatResponse:
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    finish_reason: str | None = None


@dataclass(frozen=True)
class ToolCallDelta:
    index: int
    id: str | None = None
    name: str | None = None
    arguments_fragment: str = ""


@dataclass(frozen=True)
class StreamDelta:
    text: str = ""
    tool_calls: tuple[ToolCallDelta, ...] = ()
    finish_reason: str | None = None


@dataclass
class ToolCallAccumulator:
    id: str = ""
    name: str = ""
    arguments: str = ""

    def to_call(self) -> ToolCall:
        return ToolCall(id=self.id, name=self.name, arguments=parse_json_object(self.arguments))


def parse_json_object(raw: str | None) -> dict[str, Any]:
    if not raw or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


@dataclass
class ToolCallAccumulatorBag:
    entries: dict[int, ToolCallAccumulator] = field(default_factory=dict)

    def add(self, delta: ToolCallDelta) -> None:
        entry = self.entries.setdefault(delta.index, ToolCallAccumulator())
        if delta.id:
            entry.id = delta.id
        if delta.name:
            entry.name = delta.name
        entry.arguments += delta.arguments_fragment

    def calls(self) -> tuple[ToolCall, ...]:
        return tuple(
            entry.to_call()
            for _, entry in sorted(self.entries.items())
            if entry.name
        )


class LLMProvider(ABC):
    @abstractmethod
    async def achat(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] = (),
    ) -> ChatResponse:
        """Return a complete assistant response, including any tool calls."""

    @abstractmethod
    def astream(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] = (),
    ) -> AsyncIterator[StreamDelta]:
        """Yield incremental response text and/or tool-call fragments."""

    @abstractmethod
    async def aembed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
