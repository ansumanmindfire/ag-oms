"""Routers package for AG-oms."""

from app.routers.query_router import router as query_router
from app.routers.upload_router import router as upload_router

__all__ = [
    "query_router",
    "upload_router",
]
