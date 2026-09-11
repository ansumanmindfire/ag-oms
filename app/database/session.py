"""Database engine, sessionmaker, and session dependency generator."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings

# Configure SQLite specific parameters if using SQLite
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

# Create SQLAlchemy Database Engine
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# Create SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
