"""Enquiry Agent node for LangGraph specializing in product specification search and vector RAG retrieval."""

from typing import Dict, Any
from langchain.agents import create_agent

from app.config import logger
from app.tools.enquiry_tools import SearchProductSpecsTool
from app.agents.llm_factory import get_llm
from app.prompts import ENQUIRY_AGENT_SYSTEM_PROMPT
from app.agents.state import AgentState

# Initialize tools and agent runner for the Enquiry node
tools = [SearchProductSpecsTool()]
llm = get_llm(temperature=0.1)

enquiry_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=ENQUIRY_AGENT_SYSTEM_PROMPT,
)


def enquiry_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node: handles product specifications, comparisons, and RAG retrieval."""
    logger.info("Executing Enquiry Agent node in LangGraph workflow.")
    messages = list(state.get("messages", []))
    result = enquiry_agent.invoke({"messages": messages})
    return {"messages": [result["messages"][-1]]}
