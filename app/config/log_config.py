"""Logging configuration for AG-oms application."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from app.config.env_config import settings


def setup_logger(name: str = "ag_oms") -> logging.Logger:
    """Configure and return a structured application logger."""
    app_logger = logging.getLogger(name)

    log_level = logging.DEBUG if settings.ENVIRONMENT == "DEVELOPMENT" else logging.INFO
    app_logger.setLevel(log_level)

    if not app_logger.handlers:
        os.makedirs(settings.LOG_DIR, exist_ok=True)
        log_file_path = os.path.join(settings.LOG_DIR, "app.log")

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        app_logger.addHandler(console_handler)

        # Rotating File Handler
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)

    return app_logger


# Global logger instance
logger = setup_logger()
