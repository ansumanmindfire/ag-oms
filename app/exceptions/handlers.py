"""Global FastAPI exception handlers converting domain exceptions to standardized JSON responses."""

from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import logger
from app.exceptions.custom_exceptions import BaseAppException


async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """Global handler for domain-specific BaseAppException instances."""
    logger.warning(
        f"Handled AppException [{exc.error_code}] on {request.method} {request.url.path}: {exc.message}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Global handler for standard Starlette/FastAPI HTTPExceptions."""
    logger.warning(f"HTTPException [{exc.status_code}] on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_code": "HTTP_ERROR",
            "message": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Global handler for Pydantic request validation errors."""
    logger.warning(f"Validation Error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": 422,
            "error_code": "VALIDATION_ERROR",
            "message": "Input validation failed",
            "details": exc.errors(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled internal server exceptions."""
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
