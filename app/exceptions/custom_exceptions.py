"""Custom domain exception classes for AG-oms Application."""

from typing import Optional, Any


class BaseAppException(Exception):
    """Base domain exception for the application."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class ProductNotFoundException(BaseAppException):
    """Raised when a requested product ID is not found in inventory."""

    def __init__(self, product_id: str):
        super().__init__(
            message=f"Product with ID '{product_id}' was not found in inventory.",
            status_code=404,
            error_code="PRODUCT_NOT_FOUND",
        )


class InsufficientStockException(BaseAppException):
    """Raised when inventory stock is less than the requested quantity."""

    def __init__(self, product_id: str, requested: int, available: int):
        super().__init__(
            message=f"Insufficient stock for product '{product_id}'. Requested: {requested}, Available: {available}.",
            status_code=400,
            error_code="INSUFFICIENT_STOCK",
        )


class OrderNotFoundException(BaseAppException):
    """Raised when a requested order ID is not found."""

    def __init__(self, order_id: str):
        super().__init__(
            message=f"Order with ID '{order_id}' was not found.",
            status_code=404,
            error_code="ORDER_NOT_FOUND",
        )


class InvalidOrderStatusException(BaseAppException):
    """Raised when an action is invalid for the order's current status."""

    def __init__(self, order_id: str, current_status: str, action: str):
        super().__init__(
            message=f"Cannot execute '{action}' on order '{order_id}' with current status '{current_status}'.",
            status_code=400,
            error_code="INVALID_ORDER_STATUS",
        )
