from typing import Dict, Any
from langchain_core.messages import SystemMessage

from app.config import logger
from app.constants import AGENT_TEMPERATURE
from app.graph.state import AgentState
from app.llm import get_llm
from app.tools.agent_tools import supervisor_tools
from app.prompts import SUPERVISOR_SYSTEM_PROMPT

llm = get_llm(temperature=AGENT_TEMPERATURE)
model_with_tools = llm.bind_tools(supervisor_tools)


def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """Orchestrator model node that coordinates specialist agents via agent tools.

    Args:
        state: Current graph state containing conversation messages.

    Returns:
        Dict updating messages with the LLM's response (tool call or final answer).
    """
    logger.info("Executing Orchestrator model node...")
    messages = [SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT)] + list(state.get("messages", []))
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}
