"""Health check endpoint router."""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.config.env_config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="Application version")
    status: str = Field(..., description="Health status")


@router.get("/", response_model=HealthResponse)
def health_check():
    """Return application health status"""
    return HealthResponse(
        message=f"Welcome to {settings.PROJECT_NAME}",
        version=settings.PROJECT_VERSION,
        status="healthy",
    )
