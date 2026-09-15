"""Order Agent node for LangGraph specializing in inventory stock checks and order placement."""

from typing import Dict, Any
from langchain.agents import create_agent

from app.config import logger
from app.tools.order_tools import (
    SearchProductsTool,
    CheckInventoryTool,
    PlaceOrderTool,
    SendOrderConfirmationEmailTool,
)
from app.agents.llm_factory import get_llm
from app.prompts import ORDER_AGENT_SYSTEM_PROMPT
from app.agents.state import AgentState


# Initialize tools, llm, and agent once at module startup
tools = [
    SearchProductsTool(),
    CheckInventoryTool(),
    PlaceOrderTool(),
    SendOrderConfirmationEmailTool(),
]
llm = get_llm(temperature=0.1)
order_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=ORDER_AGENT_SYSTEM_PROMPT,
)


def order_node(state: AgentState) -> Dict[str, Any]:
    """Handles inventory checks, order summaries, and order placement."""
    logger.info("Executing Order Agent node.")
    messages = list(state.get("messages", []))
    result = order_agent.invoke({"messages": messages})
    return {"messages": [result["messages"][-1]]}
