from typing import Dict, Any

from app.config import logger
from app.agents import cancellation_agent
from app.graph.state import AgentState


def cancellation_node(state: AgentState) -> Dict[str, Any]:
    """Handles customer order cancellations, audit logging, and inventory stock restoration.

    Args:
        state: Current graph state containing conversation messages.
    """
    logger.info("Executing Cancellation node...")
    messages = list(state.get("messages", []))
    result = cancellation_agent.agent.invoke({"messages": messages})
    return {"messages": [result["messages"][-1]]}
