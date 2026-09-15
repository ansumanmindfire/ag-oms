"""Email Dispatcher Service for order notifications using RedMail."""

from redmail import EmailSender
from app.config import logger, settings


class EmailService:
    """Email Delivery Service using RedMail."""

    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:
        """Core single function to dispatch an email via RedMail."""
        try:
            sender = EmailSender(
                host=settings.SMTP_SERVER,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
            )
            sender.sender = settings.SENDER_EMAIL
            sender.send(subject=subject, receivers=[to_email], text=body)
            logger.info(f"Email dispatched to '{to_email}' [Subject: '{subject}']")
            return True
        except Exception as err:
            logger.error(f"Failed to dispatch email to '{to_email}': {err}")
            return False

    @classmethod
    def send_order_confirmation_email(
        cls,
        customer_email: str,
        order_id: str,
        product_name: str,
        quantity: int,
        total_price: float,
    ) -> bool:
        """Builds order confirmation message content and dispatches email."""
        subject = f"Order Confirmation - Order #{order_id}"
        body = (
            f"Dear Customer,\n\n"
            f"Thank you for your order!\n\n"
            f"Order Details:\n"
            f"  Order ID    : {order_id}\n"
            f"  Product     : {product_name}\n"
            f"  Quantity    : {quantity}\n"
            f"  Total Price : ${total_price:,.2f}\n\n"
            f"We are processing your order and will notify you when it ships.\n\n"
            f"Best regards,\n"
            f"Agentic Order Management System Team"
        )
        return cls.send_email(to_email=customer_email, subject=subject, body=body)

    @classmethod
    def send_consolidated_order_email(
        cls,
        customer_email: str,
        orders_info: list,
    ) -> bool:
        """Builds a consolidated, itemized order confirmation email for one or multiple products."""
        if not orders_info:
            return False

        order_ids_str = ", ".join([str(item.get("order_id", "")) for item in orders_info])
        subject = f"Order Confirmation - {len(orders_info)} item(s) ordered"
        
        items_text = []
        grand_total = 0.0
        for idx, item in enumerate(orders_info, 1):
            p_name = item.get("product_name")
            qty = item.get("quantity", 1)
            u_price = float(item.get("unit_price"))
            tot = float(item.get("total_price"))
            oid = item.get("order_id")
            grand_total += tot
            items_text.append(
                f"  {idx}. {p_name}\n"
                f"     Order ID: {oid}\n"
                f"     Quantity: {qty} | Unit Price: ${u_price:,.2f} | Total: ${tot:,.2f}"
            )

        items_formatted = "\n\n".join(items_text)
        body = (
            f"Dear Customer,\n\n"
            f"Thank you for your purchase! We have received your order.\n\n"
            f"Order Receipt:\n"
            f"--------------------------------------------------\n"
            f"{items_formatted}\n"
            f"--------------------------------------------------\n"
            f"Grand Total: ${grand_total:,.2f}\n\n"
            f"Order IDs: {order_ids_str}\n\n"
            f"We are processing your order and will notify you when it ships.\n\n"
            f"Best regards,\n"
            f"Agentic Order Management System Team"
        )
        return cls.send_email(to_email=customer_email, subject=subject, body=body)

    @classmethod
    def send_cancellation_email(
        cls,
        customer_email: str,
        order_id: str,
        product_name: str,
        quantity: int,
    ) -> bool:
        """Builds cancellation confirmation message content and dispatches email."""
        subject = f"Order Cancellation Confirmation - Order #{order_id}"
        body = (
            f"Dear Customer,\n\n"
            f"Your order #{order_id} has been successfully cancelled.\n\n"
            f"Cancellation Details:\n"
            f"  Order ID    : {order_id}\n"
            f"  Product     : {product_name}\n"
            f"  Quantity    : {quantity}\n\n"
            f"Stock has been restored to our inventory and any charges have been voided.\n\n"
            f"Best regards,\n"
            f"Agentic Order Management System Team"
        )
        return cls.send_email(to_email=customer_email, subject=subject, body=body)
