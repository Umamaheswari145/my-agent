import logging
from typing import Any

from app.core.errors import AppError
from app.llm.base import ToolDefinition
from app.tools.base import Tool, ToolResult, tool_definition

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(tool_definition(tool) for tool in self._tools.values())

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(f"Unknown tool: {name}", success=False)
        problems = self._validate(tool, arguments)
        if problems:
            return ToolResult("Invalid arguments: " + "; ".join(problems), success=False)
        try:
            return await tool.run(arguments)
        except AppError as exc:
            return ToolResult(exc.detail, success=False)
        except Exception:
            logger.exception("Tool %s failed", name)
            return ToolResult("The tool failed unexpectedly.", success=False)

    @staticmethod
    def _validate(tool: Tool, arguments: dict[str, Any]) -> list[str]:
        problems: list[str] = []
        properties = tool.parameters.get("properties", {})
        required = tool.parameters.get("required", [])
        for key in required:
            if key not in arguments:
                problems.append(f"missing required field '{key}'")
        for key, value in arguments.items():
            schema = properties.get(key)
            if not isinstance(schema, dict):
                continue
            expected = schema.get("type")
            if expected == "string" and not isinstance(value, str):
                problems.append(f"'{key}' must be a string")
            elif expected == "number" and isinstance(value, bool):
                problems.append(f"'{key}' must be a number")
            elif expected == "number" and not isinstance(value, (int, float)):
                problems.append(f"'{key}' must be a number")
            elif expected == "integer" and (
                isinstance(value, bool) or not isinstance(value, int)
            ):
                problems.append(f"'{key}' must be an integer")
            elif expected == "boolean" and not isinstance(value, bool):
                problems.append(f"'{key}' must be a boolean")
        return problems
