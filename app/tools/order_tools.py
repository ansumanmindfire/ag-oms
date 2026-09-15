"""LangChain custom tools for checking inventory stock and placing orders."""

import json
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.database import SessionLocal
from app.config import logger


# Pydantic Argument Schemas for Tools

class SearchProductsInput(BaseModel):
    """Input schema for searching products in inventory."""
    query: Optional[str] = Field(
        default="",
        description=(
            "Search keyword for filtering products. If a keyword is provided (e.g., 'phone', 'laptop'), "
            "it searches and returns products matching that specific keyword. "
            "If left as an empty string '', it returns all products and their available quantities in the store inventory."
        ),
    )


class CheckInventoryInput(BaseModel):
    """Input schema for checking product inventory stock."""
    product_id: str = Field(..., description="Unique product ID (e.g., 'PROD-001')")
    quantity: int = Field(..., description="Quantity of product desired")


class PlaceOrderInput(BaseModel):
    """Input schema for placing a new customer order."""
    product_id: str = Field(..., description="Unique product ID (e.g., 'PROD-001')")
    quantity: int = Field(..., description="Quantity of product to purchase")
    customer_email: str = Field(..., description="Customer email address for order confirmation")
    remarks: Optional[str] = Field("Order placed via Agent Tool", description="Optional order remarks")


class SendOrderConfirmationEmailInput(BaseModel):
    """Input schema for dispatching a consolidated order confirmation email."""
    customer_email: str = Field(..., description="Customer email address to send the receipt to")
    order_ids: list[str] = Field(..., description="List of Order IDs to consolidate into the confirmation email")


# Custom Tools

class SearchProductsTool(BaseTool):
    """Tool for searching products in the inventory catalog by name, category, or keyword."""

    name: str = "search_inventory_products"
    description: str = (
        "Useful for querying inventory products. If query is provided with a keyword (e.g. 'phone', 'laptop', 'tv'), "
        "it searches and returns products matching that specific keyword. If query is an empty string '', "
        "it returns all products and their available quantities in the store inventory."
    )
    args_schema: Type[BaseModel] = SearchProductsInput

    def _run(self, query: Optional[str] = "") -> str:
        """Synchronous execution of product search."""
        logger.info(f"Tool execution [search_inventory_products]: query='{query}'")
        with SessionLocal() as db:
            results = InventoryService.search_products(db=db, query=query)
        return json.dumps(results, indent=2, default=str)


class CheckInventoryTool(BaseTool):
    """Tool for verifying product existence and stock availability in inventory."""

    name: str = "check_inventory_stock"
    description: str = (
        "Useful for verifying if a product exists in the inventory and whether "
        "there is sufficient stock for the requested quantity before placing an order. "
        "Returns a JSON object with keys: 'exists' (bool), 'available' (bool), 'product_id' (str), "
        "'product_name' (str), 'unit_price' (float), and 'current_stock' (int)."
    )
    args_schema: Type[BaseModel] = CheckInventoryInput

    def _run(self, product_id: str, quantity: int) -> str:
        """Synchronous execution of stock check."""
        logger.info(f"Tool execution [check_inventory_stock]: product_id='{product_id}', quantity={quantity}")
        with SessionLocal() as db:
            result = InventoryService.check_stock(db=db, product_id=product_id, quantity=quantity)
        return json.dumps(result, indent=2, default=str)


class PlaceOrderTool(BaseTool):
    """Tool for executing order placement, inventory deduction, and audit logging."""

    name: str = "place_order"
    description: str = (
        "Useful for placing a customer purchase order for a product. Atomically deducts inventory stock "
        "and creates order and audit records. Note: This tool does NOT send emails. "
        "Returns a JSON object with keys: 'success' (bool), 'order_id' (str), 'product_name' (str), "
        "'quantity' (int), 'unit_price' (float), and 'total_price' (float)."
    )
    args_schema: Type[BaseModel] = PlaceOrderInput

    def _run(
        self,
        product_id: str,
        quantity: int,
        customer_email: str,
        remarks: Optional[str] = "Order placed via Agent Tool",
    ) -> str:
        """Synchronous execution of order placement."""
        logger.info(
            f"Tool execution [place_order]: product_id='{product_id}', quantity={quantity}, email='{customer_email}'"
        )
        try:
            with SessionLocal() as db:
                result = OrderService.order_product(
                    db=db,
                    product_id=product_id,
                    quantity=quantity,
                    customer_email=customer_email,
                    remarks=remarks or "Order placed via Agent Tool",
                    send_email=False,
                )
            return json.dumps(result, indent=2, default=str)
        except Exception as err:
            logger.error(f"Error in PlaceOrderTool: {err}")
            return json.dumps({"success": False, "error": str(err)})


class SendOrderConfirmationEmailTool(BaseTool):
    """Tool for sending a single consolidated confirmation email for one or multiple placed orders."""

    name: str = "send_order_confirmation_email"
    description: str = (
        "Useful for sending a single consolidated confirmation email to the customer after all orders "
        "have been placed with place_order. Consolidates all given order_ids into one itemized receipt "
        "with grand total. Returns a JSON object with 'success' (bool), 'email_sent' (bool), and 'grand_total' (float)."
    )
    args_schema: Type[BaseModel] = SendOrderConfirmationEmailInput

    def _run(self, customer_email: str, order_ids: list[str]) -> str:
        """Synchronous execution of consolidated email dispatch."""
        logger.info(
            f"Tool execution [send_order_confirmation_email]: email='{customer_email}', order_ids={order_ids}"
        )
        try:
            with SessionLocal() as db:
                result = OrderService.send_order_confirmation(
                    db=db,
                    order_ids=order_ids,
                    customer_email=customer_email,
                )
            return json.dumps(result, indent=2, default=str)
        except Exception as err:
            logger.error(f"Error in SendOrderConfirmationEmailTool: {err}")
            return json.dumps({"success": False, "error": str(err)})

