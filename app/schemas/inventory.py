"""Pydantic V2 schemas for Inventory requests and response serialization."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.constants.constants import InventoryChangeType


class InventoryCreate(BaseModel):
    """Schema for adding a new product to inventory."""

    product_id: str = Field(..., min_length=1, max_length=50, description="Unique product ID (e.g. PROD-001)")
    product_name: str = Field(..., min_length=1, max_length=255, description="Product title or name")
    category: Optional[str] = Field(None, max_length=100, description="Product category (e.g. Laptop, Phone, TV)")
    description: Optional[str] = Field(None, description="Product feature summary description")
    quantity_available: int = Field(..., ge=0, description="Initial stock quantity available")
    price: float = Field(..., gt=0, description="Unit price of the product")


class InventoryUpdate(BaseModel):
    """Schema for updating stock or price of an existing product."""

    quantity_change: Optional[int] = Field(None, description="Positive to add stock, negative to deduct")
    price: Optional[float] = Field(None, gt=0, description="Updated price")
    remarks: Optional[str] = Field(None, description="Reason for inventory adjustment")


class InventoryResponse(BaseModel):
    """Response schema for inventory product details."""

    model_config = ConfigDict(from_attributes=True)

    product_id: str
    product_name: str
    category: Optional[str] = None
    description: Optional[str] = None
    quantity_available: int
    price: float
    last_updated: datetime


class InventoryAuditResponse(BaseModel):
    """Response schema for inventory audit log entries."""

    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    product_id: str
    change_type: InventoryChangeType
    quantity_changed: int
    timestamp: datetime
    remarks: Optional[str] = None
