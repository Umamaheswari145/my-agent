import json

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, get_optional_provider
from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit
from app.core.security import require_access_token
from app.llm.base import LLMProvider
from app.models import User
from app.schemas.conversation import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(require_access_token)],
)


def _chat_service(
    db: Session, user: User, provider: LLMProvider | None
) -> ChatService:
    return ChatService(settings, db, user, provider)


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_optional_provider),
    _rate: None = Depends(enforce_rate_limit),
) -> ChatResponse:
    return await _chat_service(db, user, provider).send(payload)


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider | None = Depends(get_optional_provider),
    _rate: None = Depends(enforce_rate_limit),
) -> Response:
    service = _chat_service(db, user, provider)

    async def events():
        async for event in service.stream(payload):
            yield f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
