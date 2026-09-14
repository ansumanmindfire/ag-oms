"""Repository encapsulation for Order and Order Audit database operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import OrderModel, OrderAuditModel
from app.exceptions.custom_exceptions import OrderNotFoundException
from app.constants.constants import OrderStatus


class OrderRepository:
    """Encapsulates pure database CRUD operations for orders and order audit logs."""

    @staticmethod
    def get_order(db: Session, order_id: str) -> Optional[OrderModel]:
        """Fetch order by ID.

        Args:
            db (Session): Database session.
            order_id (str): Order ID.

        Returns:
            Optional[OrderModel]: Order record if found, else None.
        """
        return db.query(OrderModel).filter(OrderModel.order_id == order_id).first()

    @staticmethod
    def create_order(
        db: Session,
        product_id: str,
        quantity: int,
        customer_email: str,
        remarks: str = "Order placed",
        commit: bool = True,
    ) -> OrderModel:
        """Create a new Order record and write initial order audit log.

        Args:
            db (Session): Database session.
            product_id (str): Product ID.
            quantity (int): Order quantity.
            customer_email (str): Customer email address.
            remarks (str): Remarks for order placement.
            commit (bool): Whether to immediately commit to database. Defaults to True.

        Returns:
            OrderModel: Newly created order model instance.
        """
        order = OrderModel(
            product_id=product_id,
            customer_email=customer_email,
            quantity=quantity,
            status=OrderStatus.PLACED,
            remarks=remarks,
        )
        db.add(order)
        db.flush()

        order_audit = OrderAuditModel(
            order_id=order.order_id,
            previous_status=None,
            new_status=OrderStatus.PLACED,
            remarks=f"Order created successfully for customer '{customer_email}'",
        )
        db.add(order_audit)
        if commit:
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def update_order_status(
        db: Session,
        order_id: str,
        new_status: str,
        remarks: str = "",
        commit: bool = True,
    ) -> OrderModel:
        """Update the status of an existing order and log an entry in order_audit table.

        Args:
            db (Session): Database session.
            order_id (str): Order ID.
            new_status (str): Target new status (e.g. CANCELLED).
            remarks (str): Audit remarks.
            commit (bool): Whether to immediately commit to database. Defaults to True.

        Returns:
            OrderModel: Updated order record.

        Raises:
            OrderNotFoundException: If order_id does not exist in database.
        """
        order = OrderRepository.get_order(db, order_id)
        if not order:
            raise OrderNotFoundException(order_id)

        prev_status = order.status
        order.status = new_status
        order.remarks = remarks

        order_audit = OrderAuditModel(
            order_id=order.order_id,
            previous_status=prev_status,
            new_status=new_status,
            remarks=remarks,
        )
        db.add(order_audit)
        if commit:
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def list_audits(db: Session, order_id: Optional[str] = None) -> List[OrderAuditModel]:
        """Fetch order audit trail, optionally filtered by order_id.

        Args:
            db (Session): Database session.
            order_id (Optional[str]): Optional order ID to filter audit records.

        Returns:
            List[OrderAuditModel]: List of order audit records.
        """
        query = db.query(OrderAuditModel)
        if order_id:
            query = query.filter(OrderAuditModel.order_id == order_id)
        return query.order_by(OrderAuditModel.timestamp.desc()).all()

