class AppError(Exception):
    status_code = 500
    error_code = "internal_error"

    def __init__(
        self,
        detail: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code or self.status_code
        self.error_code = error_code or self.error_code
