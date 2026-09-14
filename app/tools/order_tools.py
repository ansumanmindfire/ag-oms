"""LangChain custom tools for checking inventory stock and placing orders."""

import json
from typing import Optional, Type, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from sqlalchemy.orm import Session

from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.config import logger


# Pydantic Argument Schemas for Tools

class SearchProductsInput(BaseModel):
    """Input schema for searching products in inventory."""
    query: str = Field(..., description="Natural language search term, category, or product name (e.g., 'laptop', 'phone', 'macbook', 'shoes')")


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


# Custom Tools

class SearchProductsTool(BaseTool):
    """Tool for searching products in the inventory catalog by name, category, or keyword."""

    name: str = "search_inventory_products"
    description: str = (
        "Useful for searching the inventory catalog when the user provides a category (e.g. 'laptop', 'phone', 'tv', 'shoe', 'watch'), "
        "brand, or product keyword. Returns matching product objects with keys: "
        "'product_id', 'product_name', 'category', 'description', 'price', and 'quantity_available'."
    )
    args_schema: Type[BaseModel] = SearchProductsInput
    db: Any = Field(default=None, exclude=True)

    def _run(self, query: str) -> str:
        """Synchronous execution of product search."""
        logger.info(f"Tool execution [search_inventory_products]: query='{query}'")
        results = InventoryService.search_products(db=self.db, query=query)
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
    db: Any = Field(default=None, exclude=True)

    def _run(self, product_id: str, quantity: int) -> str:
        """Synchronous execution of stock check."""
        logger.info(f"Tool execution [check_inventory_stock]: product_id='{product_id}', quantity={quantity}")
        result = InventoryService.check_stock(db=self.db, product_id=product_id, quantity=quantity)
        return json.dumps(result, indent=2, default=str)


class PlaceOrderTool(BaseTool):
    """Tool for executing order placement, inventory deduction, audit logging, and email confirmation."""

    name: str = "place_order"
    description: str = (
        "Useful for placing a new customer purchase order. Atomically deducts inventory stock, "
        "creates order and audit records, and dispatches a customer email confirmation. "
        "Returns a JSON object with keys: 'success' (bool), 'order_id' (str), 'total_amount' (float), "
        "and 'status' (str)."
    )
    args_schema: Type[BaseModel] = PlaceOrderInput
    db: Any = Field(default=None, exclude=True)

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
            result = OrderService.order_product(
                db=self.db,
                product_id=product_id,
                quantity=quantity,
                customer_email=customer_email,
                remarks=remarks or "Order placed via Agent Tool",
            )
            return json.dumps(result, indent=2, default=str)
        except Exception as err:
            logger.error(f"Error in PlaceOrderTool: {err}")
            return json.dumps({"success": False, "error": str(err)})
