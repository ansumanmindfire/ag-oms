"""Enquiry Subgraph implementing a native ReAct loop with ToolNode."""

from typing import Dict, Any
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import logger
from app.constants import LLM_TEMPERATURE
from app.graph.state import AgentState
from app.llm import get_llm
from app.prompts import ENQUIRY_AGENT_SYSTEM_PROMPT
from app.tools.enquiry_tools import SearchProductSpecsTool


def create_enquiry_subgraph():
    """Build and compile the product enquiry specialist subgraph with native ToolNode."""
    enquiry_tools = [SearchProductSpecsTool()]
    llm = get_llm(temperature=LLM_TEMPERATURE)
    model_with_tools = llm.bind_tools(enquiry_tools)

    def enquiry_model_node(state: AgentState) -> Dict[str, Any]:
        logger.info("Executing Enquiry Subgraph model node...")
        messages = [SystemMessage(content=ENQUIRY_AGENT_SYSTEM_PROMPT)] + list(state.get("messages", []))
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("enquiry_model", enquiry_model_node)
    workflow.add_node("tools", ToolNode(enquiry_tools))

    workflow.add_edge(START, "enquiry_model")
    workflow.add_conditional_edges(
        "enquiry_model",
        tools_condition,
        {
            "tools": "tools", 
            "__end__": END
        }
    )
    workflow.add_edge("tools", "enquiry_model")

    return workflow.compile()


enquiry_subgraph = create_enquiry_subgraph()
