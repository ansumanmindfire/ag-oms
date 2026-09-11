"""Pydantic V2 schemas for Order creation, cancellation, and response serialization."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.constants.constants import OrderStatus


class OrderCreate(BaseModel):
    """Schema for creating a new order."""

    product_id: str = Field(..., min_length=1, max_length=50, description="ID of the product to order")
    quantity: int = Field(..., gt=0, description="Quantity of product to order")
    customer_email: str = Field(..., description="Customer email for confirmation")
    remarks: Optional[str] = Field("Order placed via API", description="Optional order remarks")


class OrderCancelRequest(BaseModel):
    """Schema for cancelling an order."""

    remarks: Optional[str] = Field("Order cancelled by customer", description="Cancellation reason")


class OrderResponse(BaseModel):
    """Response schema for order details."""

    model_config = ConfigDict(from_attributes=True)

    order_id: str
    product_id: str
    customer_email: str
    quantity: int
    status: OrderStatus
    remarks: Optional[str] = None
    order_date: datetime


class OrderAuditResponse(BaseModel):
    """Response schema for order audit log entries."""

    model_config = ConfigDict(from_attributes=True)

    audit_id: str
    order_id: str
    previous_status: Optional[str] = None
    new_status: str
    timestamp: datetime
    remarks: Optional[str] = None
