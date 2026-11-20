from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_db,
    get_preference_service,
)
from app.core.security import require_access_token
from app.models import User
from app.schemas.preference import PreferenceResponse, PreferenceUpdate
from app.services.preference_service import PreferenceService

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"],
    dependencies=[Depends(require_access_token)],
)


@router.get("", response_model=PreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: PreferenceService = Depends(get_preference_service),
) -> PreferenceResponse:
    return PreferenceResponse.model_validate(service.get_or_create(db, user))


@router.patch("", response_model=PreferenceResponse)
def update_preferences(
    payload: PreferenceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: PreferenceService = Depends(get_preference_service),
) -> PreferenceResponse:
    preference = service.get_or_create(db, user)
    return PreferenceResponse.model_validate(service.update(db, preference, payload))
