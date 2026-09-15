"""Order Agent node for LangGraph specializing in inventory stock checks and order placement."""

from typing import Dict, Any
from sqlalchemy.orm import Session
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


def create_order_node(db: Session):
    """Factory creating an order_node callable bound to the active database session."""
    tools = [
        SearchProductsTool(db=db),
        CheckInventoryTool(db=db),
        PlaceOrderTool(db=db),
        SendOrderConfirmationEmailTool(db=db),
    ]
    llm = get_llm(temperature=0.1)
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=ORDER_AGENT_SYSTEM_PROMPT,
    )

    def order_node(state: AgentState) -> Dict[str, Any]:
        """Handles inventory checks, order summaries, and order placement."""
        logger.info("Executing Order Agent node.")
        messages = list(state.get("messages", []))
        result = agent.invoke({"messages": messages})
        return {"messages": [result["messages"][-1]]}

    return order_node
