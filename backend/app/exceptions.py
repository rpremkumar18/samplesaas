"""Custom application exceptions mapped to HTTP responses in main.py."""


class AppError(Exception):
    """Base class for domain errors."""

    status_code: int = 500
    default_message: str = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource does not exist (or is not visible to the caller)."""

    status_code = 404
    default_message = "Resource not found"


class ConflictError(AppError):
    """Resource state conflict, e.g. duplicate email."""

    status_code = 409
    default_message = "Resource already exists"


class ForbiddenError(AppError):
    """Authenticated but not permitted."""

    status_code = 403
    default_message = "Forbidden"


class UnauthorizedError(AppError):
    """Missing or invalid credentials."""

    status_code = 401
    default_message = "Not authenticated"


class BadRequestError(AppError):
    """Invalid request not caught by schema validation."""

    status_code = 400
    default_message = "Bad request"


class ValidationFailedError(AppError):
    """Semantic validation failure, e.g. disallowed repository URL."""

    status_code = 422
    default_message = "Validation failed"


class RateLimitError(AppError):
    """Caller exceeded a rate limit."""

    status_code = 429
    default_message = "Rate limit exceeded"


class ExternalServiceError(AppError):
    """Upstream service (GitHub, OpenAI, Google) failed."""

    status_code = 502
    default_message = "Upstream service error"
