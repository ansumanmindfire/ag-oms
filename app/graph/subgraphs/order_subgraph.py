"""Order Subgraph implementing a native ReAct loop with ToolNode."""

from typing import Dict, Any
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import logger
from app.constants import LLM_TEMPERATURE
from app.graph.state import AgentState
from app.llm import get_llm
from app.prompts import ORDER_AGENT_SYSTEM_PROMPT
from app.tools.order_tools import (
    SearchProductsTool,
    CheckInventoryTool,
    PlaceOrderTool,
    SendOrderConfirmationEmailTool,
)


def create_order_subgraph():
    """Build and compile the order specialist subgraph with native ToolNode."""
    order_tools = [
        SearchProductsTool(),
        CheckInventoryTool(),
        PlaceOrderTool(),
        SendOrderConfirmationEmailTool(),
    ]
    llm = get_llm(temperature=LLM_TEMPERATURE)
    model_with_tools = llm.bind_tools(order_tools)

    def order_model_node(state: AgentState) -> Dict[str, Any]:
        logger.info("Executing Order Subgraph model node...")
        messages = [SystemMessage(content=ORDER_AGENT_SYSTEM_PROMPT)] + list(state.get("messages", []))
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("order_model", order_model_node)
    workflow.add_node("tools", ToolNode(order_tools))

    workflow.add_edge(START, "order_model")
    workflow.add_conditional_edges(
        "order_model",
        tools_condition,
        {
            "tools": "tools", 
            "__end__": END
        }
    )
    workflow.add_edge("tools", "order_model")

    return workflow.compile()


order_subgraph = create_order_subgraph()
