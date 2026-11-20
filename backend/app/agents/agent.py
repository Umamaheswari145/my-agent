from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from app.llm.base import (
    ChatMessage,
    LLMProvider,
    StreamDelta,
    ToolCallAccumulatorBag,
)
from app.tools.registry import ToolRegistry


@dataclass(frozen=True)
class AgentResult:
    content: str
    tools_used: tuple[str, ...] = ()


class AgentService:
    MAX_TOOL_ROUNDS = 5

    def __init__(self, provider: LLMProvider, registry: ToolRegistry, system_prompt: str) -> None:
        self._provider = provider
        self._registry = registry
        self._system_prompt = system_prompt

    async def run(self, messages: Sequence[ChatMessage]) -> AgentResult:
        working = self._with_system(messages)
        used: list[str] = []
        for _ in range(self.MAX_TOOL_ROUNDS):
            response = await self._provider.achat(working, self._registry.definitions())
            if not response.tool_calls:
                return AgentResult(response.content, tuple(used))
            used.extend(call.name for call in response.tool_calls)
            working.append(
                ChatMessage(role="assistant", content=response.content, tool_calls=response.tool_calls)
            )
            for call in response.tool_calls:
                result = await self._registry.execute(call.name, call.arguments)
                working.append(
                    ChatMessage(
                        role="tool",
                        content=result.output[:6000],
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )
        return AgentResult(
            "I reached the maximum number of tool steps for this request. "
            "Please try a narrower question.",
            tuple(used),
        )

    async def stream(self, messages: Sequence[ChatMessage]) -> AsyncIterator[str]:
        working = self._with_system(messages)
        for _ in range(self.MAX_TOOL_ROUNDS):
            bag = ToolCallAccumulatorBag()
            finish_reason: str | None = None
            async for delta in self._stream_deltas(working):
                if delta.text:
                    yield delta.text
                for tool_delta in delta.tool_calls:
                    bag.add(tool_delta)
                if delta.finish_reason:
                    finish_reason = delta.finish_reason

            calls = bag.calls()
            if not calls or finish_reason != "tool_calls":
                return

            working.append(ChatMessage(role="assistant", content="", tool_calls=calls))
            for call in calls:
                result = await self._registry.execute(call.name, call.arguments)
                working.append(
                    ChatMessage(
                        role="tool",
                        content=result.output[:6000],
                        tool_call_id=call.id,
                        name=call.name,
                    )
                )
        yield "I reached the maximum number of tool steps for this request. Please try a narrower question."

    async def _stream_deltas(
        self, messages: Sequence[ChatMessage]
    ) -> AsyncIterator[StreamDelta]:
        async for delta in self._provider.astream(messages, self._registry.definitions()):
            yield delta

    def _with_system(self, messages: Sequence[ChatMessage]) -> list[ChatMessage]:
        result = list(messages)
        if not result or result[0].role != "system":
            result.insert(0, ChatMessage(role="system", content=self._system_prompt))
        return result
