from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.llm.base import ToolDefinition


@dataclass(frozen=True)
class ToolResult:
    output: str
    success: bool = True


class Tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]

    @abstractmethod
    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        """Execute the tool with validated arguments."""


def tool_definition(tool: Tool) -> ToolDefinition:
    return ToolDefinition(
        name=tool.name,
        description=tool.description,
        parameters=tool.parameters,
    )
