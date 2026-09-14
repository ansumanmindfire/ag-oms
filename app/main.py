"""FastAPI application entry point for AG-oms."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import logger, settings
from app.database import engine, seed_initial_inventory
from app.models import Base
from app.exceptions import (
    BaseAppException,
    app_exception_handler,
    global_exception_handler,
    http_exception_handler,
    request_validation_handler,
)
from app.routers import query_router, upload_router
from app.services import redis_service

# Create Database tables automatically
os.makedirs("data", exist_ok=True)
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Initializing Agentic Order Management System (AG-oms)...")
    seed_initial_inventory()
    yield
    logger.info("Shutting down Agentic Order Management System (AG-oms)...")
    redis_service.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(RequestValidationError, request_validation_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(BaseAppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Register API Routers
app.include_router(query_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")


@app.get("/")
def home():
    """Health check endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.PROJECT_VERSION,
        "status": "healthy",
    }
