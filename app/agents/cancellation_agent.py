"""Cancellation Agent node for LangGraph specializing in reversing orders and restoring stock."""

from typing import Dict, Any
from sqlalchemy.orm import Session
from langchain.agents import create_agent

from app.config import logger
from app.tools.cancellation_tools import CancelOrderTool
from app.agents.llm_factory import get_llm
from app.prompts import CANCELLATION_AGENT_SYSTEM_PROMPT
from app.agents.state import AgentState


def create_cancellation_node(db: Session):
    """Factory creating a cancellation_node callable bound to the active database session."""
    tools = [CancelOrderTool(db=db)]
    llm = get_llm(temperature=0.1)
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=CANCELLATION_AGENT_SYSTEM_PROMPT,
    )

    def cancellation_node(state: AgentState) -> Dict[str, Any]:
        """Handles order cancellation workflows and stock restoration."""
        logger.info("Executing Cancellation Agent node.")
        messages = list(state.get("messages", []))
        result = agent.invoke({"messages": messages})
        return {"messages": [result["messages"][-1]]}

    return cancellation_node
