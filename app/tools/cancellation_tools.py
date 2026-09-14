"""LangChain custom tools for cancelling orders and restoring stock."""

import json
from typing import Optional, Type, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from sqlalchemy.orm import Session

from app.services.order_service import OrderService
from app.config import logger


class CancelOrderInput(BaseModel):
    """Input schema for cancelling an existing order."""
    order_id: str = Field(..., description="Unique Order ID string to cancel")
    customer_email: Optional[str] = Field(None, description="Customer email address for ownership verification")
    remarks: Optional[str] = Field("Order cancelled via Agent Tool", description="Cancellation reason")


class CancelOrderTool(BaseTool):
    """Tool for cancelling an order, restoring stock to inventory, logging audit trails, and sending email confirmation."""

    name: str = "cancel_order"
    description: str = (
        "Useful for cancelling an existing order. Atomically restores stock back to the inventory, "
        "updates order status to CANCELLED, logs audit trails, and dispatches a cancellation email. "
        "Optionally verifies customer_email ownership. "
        "Returns JSON object with keys: 'success' (bool), 'order_id' (str), 'status' (str), "
        "'quantity_restored' (int), and 'message' (str)."
    )
    args_schema: Type[BaseModel] = CancelOrderInput
    db: Any = Field(default=None, exclude=True)

    def _run(
        self,
        order_id: str,
        customer_email: Optional[str] = None,
        remarks: Optional[str] = "Order cancelled via Agent Tool",
    ) -> str:
        """Synchronous execution of order cancellation."""
        logger.info(f"Tool execution [cancel_order]: order_id='{order_id}', email='{customer_email}'")
        try:
            result = OrderService.cancel_order(
                db=self.db,
                order_id=order_id,
                customer_email=customer_email,
                remarks=remarks or "Order cancelled via Agent Tool",
            )
            return json.dumps(result, indent=2, default=str)
        except Exception as err:
            logger.error(f"Error in CancelOrderTool: {err}")
            return json.dumps({"success": False, "error": str(err)}, default=str)
