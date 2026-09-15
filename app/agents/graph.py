"""Master StateGraph for the Agentic Order Management System (LangGraph)."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from app.config import logger
from app.agents.state import AgentState
from app.agents.intent_classifier import classify_intent
from app.agents.order_agent import create_order_node
from app.agents.cancellation_agent import create_cancellation_node
from app.agents.enquiry_agent import enquiry_node
from app.agents.llm_factory import extract_text_content
from app.repositories import ChatRepository

# Global in-memory checkpointer for multi-turn session persistence
memory_checkpointer = MemorySaver()


def create_oms_graph(db: Session):
    """Builds and compiles the master Order Management System LangGraph.

    Graph Architecture:
        START -> intent_classifier
        intent_classifier --(Command)--> order_node | cancellation_node | enquiry_node | END
        order_node -> END
        cancellation_node -> END
        enquiry_node -> END
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("intent_classifier", classify_intent)
    workflow.add_node("order_node", create_order_node(db))
    workflow.add_node("cancellation_node", create_cancellation_node(db))
    workflow.add_node("enquiry_node", enquiry_node)

    # Add entry edge
    workflow.add_edge(START, "intent_classifier")

    # Connect specialist nodes to END
    workflow.add_edge("order_node", END)
    workflow.add_edge("cancellation_node", END)
    workflow.add_edge("enquiry_node", END)

    # Compile with checkpointer for automatic multi-turn state persistence
    return workflow.compile(checkpointer=memory_checkpointer)


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

    # Compile the graph with db bindings
    graph = create_oms_graph(db=db)
    config = {"configurable": {"thread_id": active_session_id}}

    # Invoke the graph with the new human message
    result = graph.invoke(
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
