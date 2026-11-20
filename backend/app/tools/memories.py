from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session

from app.models import User
from app.services.memory_service import MemoryService
from app.tools.base import Tool, ToolResult


class MemorySearchTool(Tool):
    name = "search_memories"
    description = "Retrieve relevant information previously remembered about the user."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to look for in memory."}
        },
        "required": ["query"],
    }

    def __init__(self, db: Session, user: User, service: MemoryService) -> None:
        self._db = db
        self._user = user
        self._service = service

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        memories: Sequence = await self._service.retrieve(
            self._db, self._user, arguments["query"][:400], 5
        )
        if not memories:
            return ToolResult("No relevant memories were found.")
        lines = "\n".join(f"- [{item.kind}] {item.content}" for item in memories)
        return ToolResult("Remembered information (untrusted reference data):\n" + lines)
