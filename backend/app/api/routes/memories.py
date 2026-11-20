from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_db,
    get_memory_service,
    get_optional_provider,
)
from app.api.helpers import as_uuid, paginated
from app.core.security import require_access_token
from app.llm.base import LLMProvider
from app.models import User
from app.schemas.common import PaginatedResponse
from app.schemas.memory import MemoryCreate, MemoryResponse, MemoryUpdate
from app.services.memory_service import MemoryService

router = APIRouter(
    prefix="/memories",
    tags=["memories"],
    dependencies=[Depends(require_access_token)],
)


@router.get("", response_model=PaginatedResponse[MemoryResponse])
def list_memories(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> PaginatedResponse[MemoryResponse]:
    items, total = service.list(db, user, limit, offset)
    return paginated(
        [MemoryResponse.model_validate(item) for item in items],
        total,
        limit,
        offset,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MemoryResponse)
async def create_memory(
    payload: MemoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_optional_provider),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    memory = await service.create(
        db,
        user,
        content=payload.content,
        kind=payload.kind,
        source="manual",
        provider=provider,
    )
    return MemoryResponse.model_validate(memory)


@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    payload: MemoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_optional_provider),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    memory = service.get(db, user, as_uuid(memory_id))
    updated = await service.update(
        db, memory, content=payload.content, kind=payload.kind, provider=provider
    )
    return MemoryResponse.model_validate(updated)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service),
) -> None:
    service.delete(db, service.get(db, user, as_uuid(memory_id)))
