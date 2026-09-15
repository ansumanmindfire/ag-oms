from typing import Dict, Any
from langchain.agents import create_agent

from app.config import logger
from app.tools.enquiry_tools import SearchProductSpecsTool
from app.core.llm import get_llm
from app.prompts import ENQUIRY_AGENT_SYSTEM_PROMPT
from app.graph.state import AgentState

# Initialize tools and agent runner for the Enquiry node
tools = [SearchProductSpecsTool()]
llm = get_llm(temperature=0.1)

enquiry_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=ENQUIRY_AGENT_SYSTEM_PROMPT,
)


def enquiry_node(state: AgentState) -> Dict[str, Any]:
    """Handles product technical specifications, feature comparisons, and RAG retrieval.

    Invokes the enquiry agent to search across indexed product specification
    documents and generates factual, comparative answers for the customer.

    Args:
        state: Current graph state containing conversation messages.
    """
    logger.info("Executing Enquiry node in LangGraph workflow.")
    messages = list(state.get("messages", []))
    result = enquiry_agent.invoke({"messages": messages})
    return {"messages": [result["messages"][-1]]}
