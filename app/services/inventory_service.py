"""Inventory domain business logic service."""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.repositories import InventoryRepository
from app.config import logger


class InventoryService:
    """Business logic for checking product availability and stock validation."""

    @staticmethod
    def search_products(db: Session, query: str) -> List[Dict[str, Any]]:
        """Search products in inventory matching query string.

        Args:
            db (Session): Database session.
            query (str): Search term for product name or product_id.

        Returns:
            List[Dict[str, Any]]: List of matching product summary dictionaries.
        """
        products = InventoryRepository.search_products(db, query)
        logger.info(f"Inventory search for '{query}' returned {len(products)} match(es).")
        return [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "category": p.category,
                "description": p.description,
                "quantity_available": p.quantity_available,
                "price": float(p.price) if p.price is not None else 0.0,
            }
            for p in products
        ]

    @staticmethod
    def check_stock(db: Session, product_id: str, quantity: int) -> Dict[str, Any]:

        """Check if a product exists in inventory and has sufficient stock available.

        Args:
            db (Session): Database session.
            product_id (str): Product ID.
            quantity (int): Desired purchase quantity.

        Returns:
            Dict[str, Any]: Detailed stock availability summary dictionary.
        """
        product = InventoryRepository.get_product(db, product_id)
        if not product:
            logger.warning(f"Stock check failed: Product '{product_id}' not found.")
            return {
                "available": False,
                "reason": f"Product with ID '{product_id}' does not exist in inventory.",
                "product_id": product_id,
                "quantity_requested": quantity,
                "quantity_available": 0,
                "unit_price": 0.0,
            }

        is_sufficient = product.quantity_available >= quantity
        total_price = float(product.price * quantity) if product.price is not None else 0.0

        logger.info(
            f"Stock check for '{product_id}': Requested {quantity}, Available {product.quantity_available}, Sufficient: {is_sufficient}"
        )

        return {
            "available": is_sufficient,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "quantity_requested": quantity,
            "quantity_available": product.quantity_available,
            "unit_price": float(product.price) if product.price is not None else 0.0,
            "total_estimated_price": total_price,
            "reason": "Stock is available." if is_sufficient else f"Only {product.quantity_available} unit(s) available, but {quantity} requested.",
        }
