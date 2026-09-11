"""Repository encapsulation for Chat Session and Message database operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import ChatSessionModel, ChatMessageModel


class ChatRepository:
    """Encapsulates CRUD operations for persistent chat sessions and messages."""

    @staticmethod
    def create_session(db: Session, session_name: str = "Order Management Session") -> ChatSessionModel:
        """Create a new persistent chat session record."""
        session_rec = ChatSessionModel(session_name=session_name)
        db.add(session_rec)
        db.commit()
        db.refresh(session_rec)
        return session_rec

    @staticmethod
    def get_session_by_id(db: Session, session_id: str) -> Optional[ChatSessionModel]:
        """Fetch chat session by ID."""
        return db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()

    @staticmethod
    def save_message(db: Session, session_id: str, sender: str, content: str) -> ChatMessageModel:
        """Save a single user or AI message into chat session history."""
        msg = ChatMessageModel(
            session_id=session_id,
            sender=sender,
            content=content,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_history_messages(db: Session, session_id: str, limit: int = 20) -> List[ChatMessageModel]:
        """Fetch past messages for a chat session."""
        return (
            db.query(ChatMessageModel)
            .filter(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.timestamp.asc())
            .limit(limit)
            .all()
        )
