"""SQLAlchemy ORM models for Chat Sessions and Messages."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid


class ChatSessionModel(Base):
    """Stores persistent chat session metadata for Master Orchestrator conversations."""

    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_name = Column(String(255), nullable=False, default="Order Management Session")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    messages = relationship(
        "ChatMessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessageModel.timestamp",
    )


class ChatMessageModel(Base):
    """Stores individual turns in a chat session."""

    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    sender = Column(String(20), nullable=False)  # 'user' or 'ai'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("ChatSessionModel", back_populates="messages")
