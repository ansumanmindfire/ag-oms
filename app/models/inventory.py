"""SQLAlchemy ORM models for Inventory and Inventory Audit logs."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid


class InventoryModel(Base):
    """Stores product inventory stock details."""

    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity_available >= 0", name="check_positive_stock"),
    )

    product_id = Column(String(50), primary_key=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    quantity_available = Column(Integer, nullable=False, default=0)
    price = Column(Numeric(10, 2), nullable=False)
    last_updated = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    audits = relationship("InventoryAuditModel", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("OrderModel", back_populates="product")


class InventoryAuditModel(Base):
    """Audit log tracking stock adjustments, additions, deductions, and restorations."""

    __tablename__ = "inventory_audit"

    audit_id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(50), ForeignKey("inventory.product_id"), nullable=False)
    change_type = Column(String(20), nullable=False)  # ADD, DEDUCT, RESTORE, UPDATE
    quantity_changed = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    remarks = Column(Text, nullable=True)

    # Relationships
    product = relationship("InventoryModel", back_populates="audits")
