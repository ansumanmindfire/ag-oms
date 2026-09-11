"""SQLAlchemy ORM models for Orders and Order Audit logs."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid


class OrderModel(Base):
    """Stores customer purchase order records."""

    __tablename__ = "order"

    order_id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(50), ForeignKey("inventory.product_id"), nullable=False)
    customer_email = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PLACED")  # PLACED, CANCELLED, FAILED
    remarks = Column(Text, nullable=True)
    order_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    product = relationship("InventoryModel", back_populates="orders")
    audits = relationship("OrderAuditModel", back_populates="order", cascade="all, delete-orphan")


class OrderAuditModel(Base):
    """Audit log tracking status transitions and changes for orders."""

    __tablename__ = "order_audit"

    audit_id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("order.order_id"), nullable=False)
    previous_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    remarks = Column(Text, nullable=True)

    # Relationships
    order = relationship("OrderModel", back_populates="audits")
