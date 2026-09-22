"""Application starter module creating and configuring the FastAPI application."""

import os
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.env_config import settings
from app.config.log_config import logger
from app.database import engine, seed_initial_inventory
from app.models import Base
from app.services import redis_service
from app.exceptions import (
    BaseAppException,
    app_exception_handler,
    global_exception_handler,
    http_exception_handler,
    request_validation_handler,
)
from app.constants import ROUTE_CONSTANTS
from app.health import router as health_router
from app.routers import query_router, upload_router


def init_db() -> None:
    """Create database tables and seed initial inventory."""
    Base.metadata.create_all(bind=engine)
    seed_initial_inventory()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context manager handling clean application shutdown."""
    yield
    logger.info("Shutting down Application...")
    redis_service.close()


def start_application() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app instance with middleware, routers, and DB init.
    """
    logger.info("Starting application...")
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        lifespan=lifespan,
    )

    # PATH HANDLING
    os.makedirs("data", exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    # DATABASE INITIALIZATION
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)
        raise

    # EXCEPTION HANDLERS
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(BaseAppException, app_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # CORS MIDDLEWARE
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ROUTERS
    app.include_router(health_router)
    api_v1 = APIRouter(prefix=ROUTE_CONSTANTS.API_V1_PREFIX.value)
    api_v1.include_router(query_router)
    api_v1.include_router(upload_router)
    app.include_router(api_v1)

    logger.info("Application started successfully")

    return app
