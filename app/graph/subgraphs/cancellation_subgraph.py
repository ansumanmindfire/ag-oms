"""Cancellation Subgraph implementing a native ReAct loop with ToolNode."""

from typing import Dict, Any
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import logger
from app.graph.state import AgentState
from app.core.llm import get_llm
from app.prompts import CANCELLATION_AGENT_SYSTEM_PROMPT
from app.tools.cancellation_tools import CancelOrderTool


def create_cancellation_subgraph():
    """Build and compile the cancellation specialist subgraph with native ToolNode."""
    cancellation_tools = [CancelOrderTool()]
    llm = get_llm(temperature=0.1)
    model_with_tools = llm.bind_tools(cancellation_tools)

    def cancellation_model_node(state: AgentState) -> Dict[str, Any]:
        logger.info("Executing Cancellation Subgraph model node...")
        messages = [SystemMessage(content=CANCELLATION_AGENT_SYSTEM_PROMPT)] + list(state.get("messages", []))
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("cancellation_model", cancellation_model_node)
    workflow.add_node("tools", ToolNode(cancellation_tools))

    workflow.add_edge(START, "cancellation_model")
    workflow.add_conditional_edges(
        "cancellation_model",
        tools_condition,
        {
            "tools": "tools", 
            "__end__": END
        }
    )
    workflow.add_edge("tools", "cancellation_model")

    return workflow.compile()


cancellation_subgraph = create_cancellation_subgraph()
