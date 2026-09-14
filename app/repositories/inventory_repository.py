"""Repository encapsulation for Inventory and Inventory Audit database operations."""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from app.models import InventoryModel, InventoryAuditModel
from app.schemas import InventoryCreate
from app.exceptions.custom_exceptions import ProductNotFoundException, InsufficientStockException


class InventoryRepository:
    """Encapsulates CRUD operations for inventory items and audit logs."""

    @staticmethod
    def get_product(db: Session, product_id: str) -> Optional[InventoryModel]:
        """Fetch product by ID."""
        return db.query(InventoryModel).filter(InventoryModel.product_id == product_id).first()

    @staticmethod
    def search_products(db: Session, query: str) -> List[InventoryModel]:
        """Search products by name, category, description, or product_id using case-insensitive SQL LIKE pattern."""
        if not query or not query.strip():
            return []
        search_pattern = f"%{query.strip().lower()}%"
        return (
            db.query(InventoryModel)
            .filter(
                or_(
                    func.lower(InventoryModel.product_name).like(search_pattern),
                    func.lower(InventoryModel.category).like(search_pattern),
                    func.lower(InventoryModel.description).like(search_pattern),
                    func.lower(InventoryModel.product_id).like(search_pattern),
                )
            )
            .all()
        )

    @staticmethod
    def list_products(db: Session) -> List[InventoryModel]:
        """List all inventory items."""
        return db.query(InventoryModel).all()


    @staticmethod
    def create_product(db: Session, data: InventoryCreate, commit: bool = True) -> InventoryModel:
        """Create a new product in inventory and record initial audit log."""
        product = InventoryModel(
            product_id=data.product_id,
            product_name=data.product_name,
            category=data.category,
            description=data.description,
            quantity_available=data.quantity_available,
            price=data.price,
        )
        db.add(product)
        db.flush()

        audit = InventoryAuditModel(
            product_id=data.product_id,
            change_type="ADD",
            quantity_changed=data.quantity_available,
            remarks=f"Initial inventory creation for '{data.product_name}'",
        )
        db.add(audit)
        if commit:
            db.commit()
            db.refresh(product)
        return product

    @staticmethod
    def update_stock(
        db: Session,
        product_id: str,
        quantity_change: int,
        change_type: str,
        remarks: str = "",
        commit: bool = True,
    ) -> InventoryModel:
        """Adjust stock for a product and log entry in inventory_audit table."""
        product = InventoryRepository.get_product(db, product_id)
        if not product:
            raise ProductNotFoundException(product_id)

        new_quantity = product.quantity_available + quantity_change
        if new_quantity < 0:
            raise InsufficientStockException(
                product_id=product_id,
                requested=abs(quantity_change),
                available=product.quantity_available,
            )

        product.quantity_available = new_quantity
        product.last_updated = datetime.now(timezone.utc)

        audit = InventoryAuditModel(
            product_id=product_id,
            change_type=change_type,
            quantity_changed=quantity_change,
            remarks=remarks,
        )
        db.add(audit)
        if commit:
            db.commit()
            db.refresh(product)
        return product

    @staticmethod
    def list_audits(db: Session, product_id: Optional[str] = None) -> List[InventoryAuditModel]:
        """Fetch inventory audit trail, optionally filtered by product_id."""
        query = db.query(InventoryAuditModel)
        if product_id:
            query = query.filter(InventoryAuditModel.product_id == product_id)
        return query.order_by(InventoryAuditModel.timestamp.desc()).all()
