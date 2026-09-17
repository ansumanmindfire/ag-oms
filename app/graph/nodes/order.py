from typing import Dict, Any

from app.config import logger
from app.agents import order_agent
from app.graph.state import AgentState


def order_node(state: AgentState) -> Dict[str, Any]:
    """Handles inventory checks, order summaries, and order placement workflows

    Args:
        state: Current graph state containing conversation messages.
    """
    logger.info("Executing Order node...")
    messages = list(state.get("messages", []))
    result = order_agent.agent.invoke({"messages": messages})
    return {"messages": [result["messages"][-1]]}
