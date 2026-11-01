"""Domain errors mapped to the Phase 0 error envelope (docs/API_SPECIFICATION.md 1.4)."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidRequestError(AppError):
    status_code = 400
    code = "INVALID_REQUEST"


class UnauthenticatedError(AppError):
    status_code = 401
    code = "UNAUTHENTICATED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class RevisionConflictError(AppError):
    status_code = 409
    code = "REVISION_CONFLICT"


class ValidationFailedError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class InvalidStateTransitionError(AppError):
    status_code = 422
    code = "INVALID_STATE_TRANSITION"


class PreconditionRequiredError(AppError):
    status_code = 428
    code = "PRECONDITION_REQUIRED"


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "PAYLOAD_TOO_LARGE"


class DependencyUnavailableError(AppError):
    status_code = 503
    code = "DEPENDENCY_UNAVAILABLE"


class AIUnavailableError(AppError):
    status_code = 503
    code = "AI_UNAVAILABLE"


class AIRateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMITED"


class AIValidationError(AppError):
    status_code = 422
    code = "AI_VALIDATION_ERROR"


class StaleProposalError(AppError):
    status_code = 409
    code = "STALE_PROPOSAL"
