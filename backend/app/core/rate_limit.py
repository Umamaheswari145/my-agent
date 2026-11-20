from collections import defaultdict
from threading import Lock
from time import monotonic

from fastapi import Request

from app.core.config import settings
from app.core.errors import AppError

_hits: defaultdict[str, list[float]] = defaultdict(list)
_lock = Lock()


async def enforce_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    key = f"{client}:{request.url.path}"
    now = monotonic()
    window_start = now - 60.0

    with _lock:
        hits = _hits[key]
        while hits and hits[0] <= window_start:
            hits.pop(0)

        if len(hits) >= settings.RATE_LIMIT_PER_MINUTE:
            raise AppError(
                "Rate limit exceeded. Try again shortly.",
                status_code=429,
                error_code="rate_limited",
            )

        hits.append(now)

        if len(_hits) > 10000:
            for stale_key in [item for item, values in _hits.items() if not values]:
                del _hits[stale_key]
