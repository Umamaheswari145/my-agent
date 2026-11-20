from collections.abc import Sequence
from typing import TypeVar
from uuid import UUID

from app.core.errors import AppError
from app.schemas.common import PaginatedResponse

T = TypeVar("T")


def as_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise AppError("Invalid identifier.", status_code=400, error_code="bad_request") from None


def paginated(
    items: Sequence[T], total: int, limit: int, offset: int
) -> PaginatedResponse[T]:
    return PaginatedResponse(
        items=list(items),
        total=total,
        limit=limit,
        offset=offset,
    )
