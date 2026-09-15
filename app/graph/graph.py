import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage

from app.config import settings, logger
from app.graph.state import AgentState
from app.graph.nodes import (
    classify_intent,
    order_node,
    cancellation_node,
    enquiry_node,
)
from app.core.llm import extract_text_content
from app.repositories import ChatRepository

# Ensure parent folder (/data) exists
checkpoint_path = Path(settings.CHECKPOINT_DB_PATH)
checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

# Persistent SQLite checkpointer for multi-turn session persistence
db_connection = sqlite3.connect(str(checkpoint_path), check_same_thread=False)
checkpointer = SqliteSaver(db_connection)


def create_oms_graph():

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent_classifier", classify_intent)
    workflow.add_node("order_node", order_node)
    workflow.add_node("cancellation_node", cancellation_node)
    workflow.add_node("enquiry_node", enquiry_node)

    # Add entry edge
    workflow.add_edge(START, "intent_classifier")

    # Connect specialist nodes to END
    workflow.add_edge("order_node", END)
    workflow.add_edge("cancellation_node", END)
    workflow.add_edge("enquiry_node", END)

    # Compile with checkpointer for automatic multi-turn state persistence
    return workflow.compile(checkpointer=checkpointer)


oms_graph = create_oms_graph()


def run_oms_graph(
    prompt: str,
    db: Session,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs the OMS StateGraph for a user prompt, managing session ID and conversation turns.

    Args:
        prompt: Customer's incoming text request.
        db: Active SQLAlchemy database session.
        session_id: Optional chat session ID from the client.

    Returns:
        Dict with 'session_id' and 'answer'.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    # Fetch existing session from DB or create a new one
    if session_id:
        session_rec = ChatRepository.get_session_by_id(db, session_id)
        if not session_rec:
            logger.info(f"Session '{session_id}' not found in DB. Creating new chat session.")
            session_rec = ChatRepository.create_session(db, session_name="Order Chat Session")
    else:
        session_rec = ChatRepository.create_session(db, session_name="Order Chat Session")

    active_session_id = session_rec.id
    logger.info(f"Executing LangGraph OMS workflow for session '{active_session_id}', prompt: '{prompt}'")

    config = {"configurable": {"thread_id": active_session_id}}

    # Invoke the graph with the new human message
    result = oms_graph.invoke(
        {"messages": [HumanMessage(content=prompt)]},
        config=config,
    )

    result_messages = result.get("messages", [])
    answer_text = (
        extract_text_content(result_messages[-1].content)
        if result_messages
        else "No response generated."
    )

    # Persist in DB chat tables for auditing and UI tracking
    try:
        ChatRepository.save_message(db, active_session_id, sender="user", content=prompt)
        ChatRepository.save_message(db, active_session_id, sender="ai", content=answer_text)
    except Exception as err:
        logger.warning(f"Could not persist chat message to DB: {err}")

    return {
        "session_id": active_session_id,
        "answer": answer_text,
    }
