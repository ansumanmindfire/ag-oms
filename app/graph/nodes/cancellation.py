from typing import Dict, Any
from langchain.agents import create_agent

from app.config import logger
from app.tools.cancellation_tools import CancelOrderTool
from app.core.llm import get_llm
from app.prompts import CANCELLATION_AGENT_SYSTEM_PROMPT
from app.graph.state import AgentState


# Initialize tools, llm, and agent
tools = [CancelOrderTool()]
llm = get_llm(temperature=0.1)
cancellation_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=CANCELLATION_AGENT_SYSTEM_PROMPT,
)


def cancellation_node(state: AgentState) -> Dict[str, Any]:
    """Handles customer order cancellations, audit logging, and inventory stock restoration.

    Invokes the cancellation specialist agent against incoming messages to verify order IDs,
    cancel eligible orders atomically, and notify the customer.

    Args:
        state: Current graph state containing conversation messages.
    """
    logger.info("Executing Cancellation node.")
    messages = list(state.get("messages", []))
    result = cancellation_agent.invoke({"messages": messages})
    return {"messages": [result["messages"][-1]]}
