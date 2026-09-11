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
