from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_conversation_service,
    get_current_user,
    get_db,
)
from app.api.helpers import as_uuid, paginated
from app.core.security import require_access_token
from app.models import User
from app.schemas.common import PaginatedResponse
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    dependencies=[Depends(require_access_token)],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ConversationResponse)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    conversation = service.create(db, user, payload.title)
    return ConversationResponse.model_validate(conversation)


@router.get("", response_model=PaginatedResponse[ConversationResponse])
def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    query: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> PaginatedResponse[ConversationResponse]:
    items, total = service.list(db, user, limit, offset, query)
    return paginated(
        [ConversationResponse.model_validate(item) for item in items],
        total,
        limit,
        offset,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    conversation = service.get(db, user, as_uuid(conversation_id))
    return ConversationResponse.model_validate(conversation)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def rename_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    conversation = service.get(db, user, as_uuid(conversation_id))
    return ConversationResponse.model_validate(service.rename(db, conversation, payload.title))


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> None:
    service.delete(db, service.get(db, user, as_uuid(conversation_id)))


@router.get("/{conversation_id}/messages", response_model=PaginatedResponse[MessageResponse])
def list_messages(
    conversation_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
) -> PaginatedResponse[MessageResponse]:
    conversation = service.get(db, user, as_uuid(conversation_id))
    items, total = service.messages(db, conversation, limit, offset)
    return paginated(
        [MessageResponse.model_validate(item) for item in items],
        total,
        limit,
        offset,
    )
