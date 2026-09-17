from typing import Dict, Any

from app.config import logger
from app.agents import enquiry_agent
from app.graph.state import AgentState


def enquiry_node(state: AgentState) -> Dict[str, Any]:
    """Handles product technical specifications, feature comparisons, and RAG retrieval.

    Args:
        state: Current graph state containing conversation messages.
    """
    logger.info("Executing Enquiry node...")
    messages = list(state.get("messages", []))
    result = enquiry_agent.agent.invoke({"messages": messages})
    return {"messages": [result["messages"][-1]]}
