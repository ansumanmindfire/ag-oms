"""Order domain business logic service combining database operations and email delivery."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories import OrderRepository, InventoryRepository
from app.services.email_service import EmailService
from app.exceptions.custom_exceptions import (
    OrderNotFoundException,
    InvalidOrderStatusException,
    ProductNotFoundException,
    InsufficientStockException,
    OrderOwnershipException,
)
from app.constants.constants import OrderStatus
from app.config import logger


class OrderService:
    """Business logic service for orchestrating order placement, cancellation, stock changes, and email notifications."""

    @staticmethod
    def order_product(
        db: Session,
        product_id: str,
        quantity: int,
        customer_email: str,
        remarks: str = "Order placed via Agent",
        send_email: bool = False,
    ) -> Dict[str, Any]:
        """Process a new product order placement with atomic inventory deduction.

        Args:
            db (Session): Database session.
            product_id (str): ID of product to order.
            quantity (int): Units requested.
            customer_email (str): Email address of customer.
            remarks (str): Optional remarks string. Defaults to "Order placed via Agent".
            send_email (bool): Whether to dispatch email immediately. Defaults to False.

        Returns:
            Dict[str, Any]: Execution details dictionary summarizing order status.

        Raises:
            ProductNotFoundException: If product_id does not exist in inventory.
            InsufficientStockException: If available stock is less than requested quantity.
        """
        logger.info(f"Processing order placement for product '{product_id}', Qty: {quantity}, Email: '{customer_email}'")

        # Fetch and validate product existence
        product = InventoryRepository.get_product(db, product_id)
        if not product:
            raise ProductNotFoundException(product_id)

        # Validate inventory stock availability
        if product.quantity_available < quantity:
            raise InsufficientStockException(
                product_id=product_id,
                requested=quantity,
                available=product.quantity_available,
            )

        product_name = product.product_name
        unit_price = float(product.price)
        total_price = unit_price * quantity

        # Atomic transaction: Deduct stock, create order, and log audits
        try:
            InventoryRepository.update_stock(
                db=db,
                product_id=product_id,
                quantity_change=-quantity,
                change_type="DEDUCT",
                remarks=f"Stock deducted for order placement ({quantity} unit(s))",
                commit=False,
            )

            order = OrderRepository.create_order(
                db=db,
                product_id=product_id,
                quantity=quantity,
                customer_email=customer_email,
                remarks=remarks,
                commit=False,
            )

            db.commit()
            db.refresh(order)
        except Exception as err:
            db.rollback()
            logger.error(f"Failed to place order atomically: {err}")
            raise err

        email_sent = False
        if send_email:
            email_sent = EmailService.send_order_confirmation_email(
                customer_email=customer_email,
                order_id=order.order_id,
                product_name=product_name,
                quantity=quantity,
                total_price=total_price,
            )

        return {
            "success": True,
            "order_id": order.order_id,
            "product_id": order.product_id,
            "product_name": product_name,
            "quantity": order.quantity,
            "unit_price": unit_price,
            "status": order.status,
            "customer_email": order.customer_email,
            "total_price": float(total_price) if total_price is not None else 0.0,
            "email_sent": email_sent,
            "message": f"Order #{order.order_id} placed successfully for {quantity} unit(s) of '{product_name}'.",
        }

    @staticmethod
    def send_order_confirmation(
        db: Session,
        order_ids: list,
        customer_email: str,
    ) -> Dict[str, Any]:
        """Aggregate order details across one or multiple order IDs and dispatch a single consolidated email.

        Args:
            db (Session): Database session.
            order_ids (list): List of order IDs to consolidate.
            customer_email (str): Target customer email address.

        Returns:
            Dict[str, Any]: Confirmation details including items consolidated, grand total, and email status.
        """
        logger.info(f"Sending consolidated order confirmation email for Order IDs: {order_ids} to '{customer_email}'")

        orders_info = []
        grand_total = 0.0

        for oid in order_ids:
            oid_str = str(oid).strip()
            order_rec = OrderRepository.get_order(db, oid_str)
            if not order_rec:
                continue

            product = InventoryRepository.get_product(db, order_rec.product_id)
            p_name = product.product_name if product else order_rec.product_id
            u_price = float(product.price) if product else 0.0
            tot = u_price * order_rec.quantity
            grand_total += tot

            orders_info.append({
                "order_id": order_rec.order_id,
                "product_name": p_name,
                "quantity": order_rec.quantity,
                "unit_price": u_price,
                "total_price": tot,
            })

        if not orders_info:
            return {
                "success": False,
                "email_sent": False,
                "error": "No valid order records found for the provided Order IDs.",
            }

        email_sent = EmailService.send_consolidated_order_email(
            customer_email=customer_email,
            orders_info=orders_info,
        )

        return {
            "success": True,
            "email_sent": email_sent,
            "customer_email": customer_email,
            "order_count": len(orders_info),
            "grand_total": grand_total,
            "items": orders_info,
            "message": f"Consolidated confirmation email dispatched to '{customer_email}' for {len(orders_info)} item(s) (Grand Total: ${grand_total:,.2f}).",
        }

    @staticmethod
    def cancel_order(
        db: Session,
        order_id: str,
        customer_email: Optional[str] = None,
        remarks: str = "Order cancelled via Agent",
    ) -> Dict[str, Any]:
        """Process an order cancellation: update order status, restore inventory stock, and send cancellation email.

        Args:
            db (Session): Database session.
            order_id (str): ID of order to cancel.
            customer_email (Optional[str]): Customer email for ownership verification.
            remarks (str): Reason/remarks for cancellation. Defaults to "Order cancelled via Agent".

        Returns:
            Dict[str, Any]: Execution details dictionary summarizing cancellation and stock restoration.

        Raises:
            OrderNotFoundException: If order_id does not exist in database.
            InvalidOrderStatusException: If order is already in CANCELLED status.
            OrderOwnershipException: If customer_email does not match order record.
        """
        logger.info(f"Processing order cancellation for Order ID '{order_id}', Customer Email: '{customer_email}'")

        # Fetch and validate existing order
        existing_order = OrderRepository.get_order(db, order_id)
        if not existing_order:
            raise OrderNotFoundException(order_id)

        # Validate ownership if email provided
        if customer_email and customer_email.strip():
            if existing_order.customer_email.strip().lower() != customer_email.strip().lower():
                raise OrderOwnershipException(order_id)

        # Validate current order status
        if existing_order.status == OrderStatus.CANCELLED:
            raise InvalidOrderStatusException(
                order_id=order_id,
                current_status=existing_order.status,
                action="cancellation",
            )

        recorded_email = existing_order.customer_email
        quantity = existing_order.quantity
        product_id = existing_order.product_id

        # Fetch product details for email dispatch
        product = InventoryRepository.get_product(db, product_id)
        product_name = product.product_name if product else product_id

        # Atomic transaction: update order status to CANCELLED and restore stock
        try:
            cancelled_order = OrderRepository.update_order_status(
                db=db,
                order_id=order_id,
                new_status=OrderStatus.CANCELLED,
                remarks=remarks,
                commit=False,
            )

            InventoryRepository.update_stock(
                db=db,
                product_id=product_id,
                quantity_change=quantity,
                change_type="RESTORE",
                remarks=f"Stock restored due to cancellation of order '{order_id}'",
                commit=False,
            )

            db.commit()
            db.refresh(cancelled_order)
        except Exception as err:
            db.rollback()
            logger.error(f"Failed to cancel order atomically: {err}")
            raise err

        # Send cancellation confirmation email to customer after commit
        email_sent = False
        if recorded_email:
            email_sent = EmailService.send_cancellation_email(
                customer_email=recorded_email,
                order_id=order_id,
                product_name=product_name,
                quantity=quantity,
            )

        return {
            "success": True,
            "order_id": cancelled_order.order_id,
            "product_id": cancelled_order.product_id,
            "product_name": product_name,
            "status": cancelled_order.status,
            "quantity_restored": quantity,
            "customer_email": recorded_email,
            "email_sent": email_sent,
            "message": f"Order #{order_id} cancelled successfully. Restored {quantity} unit(s) to inventory stock.",
        }

