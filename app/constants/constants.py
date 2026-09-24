"""Application constants and enumerations for AG-oms."""

from enum import Enum
from typing import Dict


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


class ROUTE_CONSTANTS(str, Enum):
    """Route path and prefix constants."""
    API_V1_PREFIX = "/api/v1"


# LLM Temperature Configurations
LLM_TEMPERATURE: float = 0.1
AGENT_TEMPERATURE: float = 0.0
LLM_MAX_TOKENS: int = 800


# Streaming Tool Execution Status Messages
TOOL_STATUS_MESSAGES: Dict[str, str] = {
    "call_order_agent": "Checking inventory...",
    "call_enquiry_agent": "Searching product specifications...",
    "call_cancellation_agent": "Checking orders...",
}
