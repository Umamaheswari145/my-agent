from hmac import compare_digest

from fastapi import Header

from app.core.config import settings
from app.core.errors import AppError


async def require_access_token(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    expected = settings.APP_ACCESS_TOKEN.get_secret_value()

    if not expected:
        raise AppError(
            "APP_ACCESS_TOKEN is not configured on the server.",
            status_code=503,
            error_code="auth_not_configured",
        )

    if x_api_key is None or not compare_digest(x_api_key, expected):
        raise AppError(
            "A valid API key is required.",
            status_code=401,
            error_code="unauthorized",
        )
