"""Declarative base class and helper utilities for ORM models."""

import uuid
from sqlalchemy.orm import declarative_base

# Base declarative class for ORM models
Base = declarative_base()


def generate_uuid() -> str:
    """Generates a string UUID hex representation.

    Returns:
        str: Unique UUID string.
    """
    return uuid.uuid4().hex
