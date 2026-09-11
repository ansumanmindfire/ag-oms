"""Application constants and enumerations for AG-oms."""

from enum import Enum


class OrderStatus(str, Enum):
    """Order status values."""
    PLACED = "PLACED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class InventoryChangeType(str, Enum):
    """Inventory audit change types."""
    ADD = "ADD"
    DEDUCT = "DEDUCT"
    RESTORE = "RESTORE"
    UPDATE = "UPDATE"
