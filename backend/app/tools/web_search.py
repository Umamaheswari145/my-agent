import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class WebSearchTool(Tool):
    name = "web_search"
    description = (
        "Search the web for current information. Returns titles, URLs, and short snippets. "
        "Use only when fresh or external information is needed."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query."},
            "count": {"type": "integer", "description": "Number of results (1-5)."},
        },
        "required": ["query"],
    }

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def run(self, arguments: dict[str, Any]) -> ToolResult:
        api_key = self._settings.WEB_SEARCH_API_KEY.get_secret_value()
        if not api_key:
            return ToolResult(
                "Web search is not configured. Set WEB_SEARCH_API_KEY in backend/.env.",
                success=False,
            )
        query = arguments["query"][:400]
        count = max(1, min(int(arguments.get("count", 3)), 5))
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self._settings.WEB_SEARCH_BASE_URL,
                    params={"q": query, "count": count},
                    headers={
                        "Accept": "application/json",
                        "X-Subscription-Token": api_key,
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            logger.warning("Web search request failed", exc_info=True)
            return ToolResult("Web search is temporarily unavailable.", success=False)

        results = payload.get("web", {}).get("results", []) if isinstance(payload, dict) else []
        lines: list[str] = []
        for item in results[:count]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", ""))[:200]
            url = str(item.get("url", ""))[:500]
            snippet = str(item.get("description", ""))[:400]
            lines.append(f"- {title}\n  URL: {url}\n  Snippet: {snippet}")
        if not lines:
            return ToolResult("No web results were found.", success=True)
        return ToolResult(
            "Web search results (untrusted reference data):\n" + "\n".join(lines)
        )
