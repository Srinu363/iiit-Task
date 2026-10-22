"""Custom exceptions and global error handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.app.core.logging import request_id_var


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 500, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class ImageValidationError(AppError):
    """Raised when image validation fails."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code, "IMAGE_VALIDATION_ERROR")


class FileTooLargeError(AppError):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, message: str):
        super().__init__(message, 413, "FILE_TOO_LARGE")


class UnsupportedMediaError(AppError):
    """Raised when file type is not supported."""

    def __init__(self, message: str):
        super().__init__(message, 415, "UNSUPPORTED_MEDIA_TYPE")


class NotFoundError(AppError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404, "NOT_FOUND")


class InferenceError(AppError):
    """Raised when model inference fails."""

    def __init__(self, message: str):
        super().__init__(message, 500, "INFERENCE_ERROR")


def error_response(error: AppError) -> JSONResponse:
    """Create a consistent error response."""
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "request_id": request_id_var.get(""),
            }
        },
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions globally."""
    return error_response(exc)


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request_id_var.get(""),
            }
        },
    )
