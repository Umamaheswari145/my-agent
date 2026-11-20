from collections.abc import AsyncIterator, Sequence

from app.llm.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    StreamDelta,
    ToolCall,
    ToolDefinition,
)


class FakeProvider(LLMProvider):
    def __init__(
        self,
        responses: Sequence[ChatResponse] | None = None,
        stream: Sequence[StreamDelta] | None = None,
    ) -> None:
        self.responses = list(responses or [ChatResponse(content="Fake answer.")])
        self.stream = list(stream or [])
        self.chat_calls: list[list[ChatMessage]] = []
        self.stream_calls: list[list[ChatMessage]] = []
        self.embed_calls: list[list[str]] = []

    async def achat(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] = (),
    ) -> ChatResponse:
        self.chat_calls.append(list(messages))
        index = min(len(self.chat_calls) - 1, len(self.responses) - 1)
        return self.responses[index]

    async def astream(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] = (),
    ) -> AsyncIterator[StreamDelta]:
        self.stream_calls.append(list(messages))
        for delta in self.stream:
            yield delta

    async def aembed(self, texts: Sequence[str]) -> list[list[float]]:
        self.embed_calls.append(list(texts))
        return [self._vector(text) for text in texts]

    @staticmethod
    def _vector(text: str) -> list[float]:
        lowered = text.lower()
        return [
            float(lowered.count("python")),
            float(lowered.count("sql")),
            float(len(lowered) % 7),
            1.0,
        ]


def tool_call_response(name: str, arguments: dict[str, object], call_id: str = "call-1") -> ChatResponse:
    return ChatResponse(
        content="",
        tool_calls=(ToolCall(id=call_id, name=name, arguments=arguments),),
        finish_reason="tool_calls",
    )
