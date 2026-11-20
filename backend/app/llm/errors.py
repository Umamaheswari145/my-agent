from app.core.errors import AppError


class ProviderError(AppError):
    status_code = 502
    error_code = "llm_error"

    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=self.status_code, error_code=self.error_code)


class ProviderNotConfiguredError(ProviderError):
    status_code = 503
    error_code = "llm_not_configured"


class ProviderAuthError(ProviderError):
    status_code = 502
    error_code = "llm_auth_failed"


class ProviderRateLimitError(ProviderError):
    status_code = 429
    error_code = "llm_rate_limited"


class ProviderQuotaError(ProviderError):
    status_code = 402
    error_code = "llm_quota_exceeded"


class ProviderTimeoutError(ProviderError):
    status_code = 504
    error_code = "llm_timeout"


class ProviderModelError(ProviderError):
    status_code = 502
    error_code = "llm_model_unavailable"


class ProviderUnavailableError(ProviderError):
    status_code = 503
    error_code = "llm_unavailable"


class ProviderResponseError(ProviderError):
    status_code = 502
    error_code = "llm_invalid_response"
