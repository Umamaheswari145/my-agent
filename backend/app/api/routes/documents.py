from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_db,
    get_document_service,
    get_optional_provider,
)
from app.api.helpers import as_uuid, paginated
from app.core.security import require_access_token
from app.llm.base import LLMProvider
from app.models import User
from app.schemas.common import PaginatedResponse
from app.schemas.document import (
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
)
from app.services.document_service import DocumentService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_access_token)],
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_optional_provider),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    data = await file.read()
    document = await service.upload(
        db, user, filename=file.filename or "document", data=data, provider=provider
    )
    return DocumentResponse.model_validate(document)


@router.get("", response_model=PaginatedResponse[DocumentResponse])
def list_documents(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> PaginatedResponse[DocumentResponse]:
    items, total = service.list(db, user, limit, offset)
    return paginated(
        [DocumentResponse.model_validate(item) for item in items],
        total,
        limit,
        offset,
    )


@router.post("/search", response_model=list[DocumentSearchResult])
async def search_documents(
    payload: DocumentSearchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_optional_provider),
    service: DocumentService = Depends(get_document_service),
) -> list[DocumentSearchResult]:
    return await service.search(db, user, payload.query, payload.limit, provider)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
) -> None:
    service.delete(db, service.get(db, user, as_uuid(document_id)))
