from typing import Dict, Any
from langchain.agents import create_agent

from app.config import logger
from app.tools.order_tools import (
    SearchProductsTool,
    CheckInventoryTool,
    PlaceOrderTool,
    SendOrderConfirmationEmailTool,
)
from app.core.llm import get_llm
from app.prompts import ORDER_AGENT_SYSTEM_PROMPT
from app.graph.state import AgentState


# Initialize tools, llm, and agent
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
    """Handles inventory checks, order summaries, and order placement workflows.

    Invokes the specialized ReAct order agent with the conversation history and
    available order management tools. Returns the final AI message to append to state.

    Args:
        state: Current graph state containing conversation messages.
    """
    logger.info("Executing Order node.")
    messages = list(state.get("messages", []))
    result = order_agent.invoke({"messages": messages})
    return {"messages": [result["messages"][-1]]}
