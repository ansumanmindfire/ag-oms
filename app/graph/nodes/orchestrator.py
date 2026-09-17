"""Orchestrator node for LangGraph workflow routing using Command(goto=...)."""

from typing import Literal, Optional
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import AIMessage

from app.config import logger
from app.graph.state import AgentState
from app.agents.orchestrator_agent import orchestrator_agent, RouteDecision


def orchestrator_node(
    state: AgentState,
) -> Command[Literal["order_subgraph", "cancellation_subgraph", "enquiry_subgraph", END]]:
    """
    Args:
        state: Current graph state containing conversation messages.

    Returns:
        Command specifying the next node to execute or END with reply.
    """
    messages = list(state.get("messages", []))
    logger.info("Executing Orchestrator node...")

    result = orchestrator_agent.agent.invoke({"messages": messages})
    decision: Optional[RouteDecision] = result.get("structured_response")

    destination = decision.destination if decision else "general_reply"
    reply = decision.reply if decision else None

    logger.info(f"Orchestrator Agent routed to destination: '{destination}'")

    if destination not in ["order_subgraph", "cancellation_subgraph", "enquiry_subgraph"]:
        greeting_text = (
            reply
            or "Hi! I am your AI assistant for the Order Management System. How can I assist you today?"
        )
        return Command(
            update={"messages": [AIMessage(content=greeting_text)]},
            goto=END,
        )

    return Command(goto=destination)
