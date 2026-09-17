import uuid
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from app.config import logger
from app.graph.state import AgentState
from app.graph.checkpointer import checkpointer
from app.graph.nodes import orchestrator_node
from app.graph.subgraphs import (
    order_subgraph,
    cancellation_subgraph,
    enquiry_subgraph,
)
from app.core.llm import extract_text_content


def create_oms_graph():

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("orchestrator_node", orchestrator_node)
    workflow.add_node("order_subgraph", order_subgraph)
    workflow.add_node("cancellation_subgraph", cancellation_subgraph)
    workflow.add_node("enquiry_subgraph", enquiry_subgraph)

    # Add entry edge
    workflow.add_edge(START, "orchestrator_node")

    # Connect specialist subgraphs to END
    workflow.add_edge("order_subgraph", END)
    workflow.add_edge("cancellation_subgraph", END)
    workflow.add_edge("enquiry_subgraph", END)

    # Compile with checkpointer for automatic multi-turn state persistence
    return workflow.compile(checkpointer=checkpointer)


oms_graph = create_oms_graph()
oms_graph.print_ascii()

def run_oms_graph(
    prompt: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs the OMS StateGraph for a user prompt, managing session ID and conversation turns.

    Args:
        prompt: Customer's incoming text request.
        session_id: Optional chat session ID from the client.

    Returns:
        Dict with 'session_id' and 'answer'.
    """

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    # Use client-provided session_id or generate a new unique session thread ID
    active_session_id = session_id.strip() if (session_id and session_id.strip()) else str(uuid.uuid4())
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

    return {
        "session_id": active_session_id,
        "answer": answer_text,
    }

