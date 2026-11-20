from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, UserPreference
from app.schemas.preference import PreferenceUpdate


class PreferenceService:
    def get_or_create(self, db: Session, user: User) -> UserPreference:
        preference = db.scalar(
            select(UserPreference).where(UserPreference.user_id == user.id)
        )
        if preference is not None:
            user.preference = preference
            return preference
        preference = UserPreference(user_id=user.id)
        db.add(preference)
        db.commit()
        db.refresh(preference)
        user.preference = preference
        return preference

    def update(
        self, db: Session, preference: UserPreference, changes: PreferenceUpdate
    ) -> UserPreference:
        for field, value in changes.model_dump(exclude_unset=True).items():
            setattr(preference, field, value)
        db.commit()
        db.refresh(preference)
        return preference

    @staticmethod
    def instructions(preference: UserPreference) -> str:
        lines = [
            f"Preferred response style: {preference.response_style}.",
            f"Tone: {preference.tone}.",
            f"Answer length: {preference.verbosity}.",
        ]
        if preference.extra_instructions.strip():
            lines.append(f"User's additional instructions: {preference.extra_instructions.strip()}")
        return "\n".join(lines)
