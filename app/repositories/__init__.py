"""Repositories package for AG-oms."""

from app.repositories.inventory_repository import InventoryRepository
from app.repositories.order_repository import OrderRepository

__all__ = [
    "InventoryRepository",
    "OrderRepository",
]

