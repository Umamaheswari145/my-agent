from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_db,
    get_model_config_service,
)
from app.core.config import settings
from app.core.security import require_access_token
from app.models import User
from app.schemas.model_config import AIModelConfigResponse, AIModelConfigUpdate
from app.services.model_config_service import ModelConfigService

router = APIRouter(
    prefix="/model-config",
    tags=["model-config"],
    dependencies=[Depends(require_access_token)],
)


@router.get("", response_model=AIModelConfigResponse)
def get_model_config(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ModelConfigService = Depends(get_model_config_service),
) -> AIModelConfigResponse:
    return AIModelConfigResponse.model_validate(service.get_or_create(db, user, settings))


@router.patch("", response_model=AIModelConfigResponse)
def update_model_config(
    payload: AIModelConfigUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: ModelConfigService = Depends(get_model_config_service),
) -> AIModelConfigResponse:
    config = service.get_or_create(db, user, settings)
    return AIModelConfigResponse.model_validate(service.update(db, config, payload))
