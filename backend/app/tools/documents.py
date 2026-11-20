from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import User
from app.services.document_service import DocumentService
from app.tools.base import Tool, ToolResult


class DocumentSearchTool(Tool):
    name = "search_documents"
    description = "Search the user's uploaded documents for relevant passages."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to find in the documents."},
            "limit": {"type": "integer", "description": "Maximum number of passages (1-10)."},
        },
        "required": ["query"],
    }

    def __init__(
        self, db: Session, user: User, service: DocumentService, settings: Settings
    ) -> None:
        self._db = db
        self._user = user
        self._service = service
        self._settings = settings

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        limit = max(1, min(int(arguments.get("limit", self._settings.DOCUMENT_TOP_K)), 10))
        results = await self._service.search(
            self._db, self._user, arguments["query"][:500], limit
        )
        if not results:
            return ToolResult("No matching document passages were found.")
        lines = "\n".join(
            f"- [{item.filename}, chunk {item.chunk_index}, score {item.score:.2f}] "
            f"{item.content}"[:1500]
            for item in results
        )
        return ToolResult("Document excerpts (untrusted reference data):\n" + lines)
