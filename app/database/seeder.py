"""Database seeding utilities for initial product inventory and sample data across 5 categories."""

from app.config import logger
from app.database.session import SessionLocal
from app.repositories import InventoryRepository
from app.schemas import InventoryCreate


def seed_initial_inventory() -> None:
    """Seed initial sample products across 5 categories if inventory table is empty."""
    with SessionLocal() as db:
        existing = InventoryRepository.list_products(db)
        if not existing:
            logger.info("Seeding initial product inventory across 5 categories (10 products)...")
            sample_products = [
                # Category 1: Laptop
                InventoryCreate(
                    product_id="PROD-001",
                    product_name="MacBook Pro M3",
                    category="Laptop",
                    description="16-inch Liquid Retina XDR display, Apple M3 Max chip, 36GB Unified Memory, 1TB SSD.",
                    quantity_available=25,
                    price=1999.00,
                ),
                InventoryCreate(
                    product_id="PROD-002",
                    product_name="Asus ROG Strix 15",
                    category="Laptop",
                    description="15.6-inch 300Hz QHD gaming laptop, Intel Core i9, NVIDIA RTX 4080, 32GB RAM, 1TB SSD.",
                    quantity_available=30,
                    price=1499.00,
                ),
                # Category 2: Phone
                InventoryCreate(
                    product_id="PROD-003",
                    product_name="iPhone 17 Pro",
                    category="Phone",
                    description="6.3-inch Super Retina XDR display, A19 Pro chip, titanium design, 48MP triple camera.",
                    quantity_available=40,
                    price=1199.00,
                ),
                InventoryCreate(
                    product_id="PROD-004",
                    product_name="Samsung Galaxy S25 Ultra",
                    category="Phone",
                    description="6.8-inch Dynamic AMOLED 2X, Snapdragon 8 Gen 4, built-in S Pen, 200MP camera system.",
                    quantity_available=35,
                    price=1299.00,
                ),
                # Category 3: TV
                InventoryCreate(
                    product_id="PROD-005",
                    product_name="Sony Bravia OLED 65",
                    category="TV",
                    description="65-inch 4K HDR OLED Google TV with Acoustic Surface Audio+ and Cognitive Processor XR.",
                    quantity_available=20,
                    price=1799.00,
                ),
                InventoryCreate(
                    product_id="PROD-006",
                    product_name="Motorola Smart TV 55",
                    category="TV",
                    description="55-inch 4K Ultra HD Smart LED TV with Dolby Vision, Atmos, and Android TV OS.",
                    quantity_available=50,
                    price=599.00,
                ),
                # Category 4: Shoe
                InventoryCreate(
                    product_id="PROD-007",
                    product_name="Nike X23 Running Shoes",
                    category="Shoe",
                    description="Lightweight ZoomX foam cushioning running shoes for high distance marathon endurance.",
                    quantity_available=100,
                    price=149.00,
                ),
                InventoryCreate(
                    product_id="PROD-008",
                    product_name="Puma C23 Pro Sneakers",
                    category="Shoe",
                    description="Retro lifestyle street sneakers with SoftFoam+ comfort sockliner and durable rubber sole.",
                    quantity_available=80,
                    price=119.00,
                ),
                # Category 5: Watch
                InventoryCreate(
                    product_id="PROD-009",
                    product_name="G-Shock MTG-B4000BD-1A",
                    category="Watch",
                    description="Tough solar Bluetooth radio-controlled dual-core guard structure chronograph wristwatch.",
                    quantity_available=15,
                    price=450.00,
                ),
                InventoryCreate(
                    product_id="PROD-010",
                    product_name="Tissot PR100 Classic",
                    category="Watch",
                    description="Swiss quartz movement classic analog dress watch with scratch-resistant sapphire crystal.",
                    quantity_available=25,
                    price=350.00,
                ),
            ]
            for prod in sample_products:
                InventoryRepository.create_product(db, prod)
            logger.info(f"Successfully seeded {len(sample_products)} products across 5 categories into inventory.")
