"""Cancellation Agent service specializing in reversing orders and restoring stock."""

from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.agents import create_agent
from sqlalchemy.orm import Session

from app.config import settings, logger
from app.tools.cancellation_tools import CancelOrderTool
from app.agents.llm_factory import get_llm


CANCELLATION_AGENT_SYSTEM_PROMPT = (
    "You are the Cancellation Agent for an Agentic Order Management System.\n"
    "Your responsibility is to assist customers with cancelling existing orders and restoring stock.\n\n"
    "Behavior Guidelines:\n"
    "- If the order_id is missing or invalid, ask the user to provide a valid Order ID.\n"
    "- Always execute order cancellation when a valid Order ID is provided.\n"
    "- Provide a polite, clear confirmation summarizing the cancellation and stock restoration."
)


class CancellationAgent:
    """Specialized Agent for handling order cancellation workflows using create_agent."""

    def __init__(self, db: Session):
        self.db = db
        self.tools = [CancelOrderTool(db=self.db)]
        self._llm = get_llm(temperature=0.1)

        self.agent = create_agent(
            model=self._llm,
            tools=self.tools,
            system_prompt=CANCELLATION_AGENT_SYSTEM_PROMPT,
        )

    def run(self, prompt: str, history: List[BaseMessage] = None) -> Dict[str, Any]:
        """Execute the Cancellation Agent via create_agent harness.

        Args:
            prompt (str): Natural language customer request.
            history (List[BaseMessage]): Previous conversation history.

        Returns:
            Dict[str, Any]: Agent response dictionary with final answer string.
        """
        logger.info(f"Running Cancellation Agent via create_agent for prompt: '{prompt}'")

        messages: List[BaseMessage] = list(history) if history else []
        messages.append(HumanMessage(content=prompt))

        result = self.agent.invoke({"messages": messages})
        result_messages = result.get("messages", [])

        final_answer = str(result_messages[-1].content) if result_messages else ""
        return {"answer": final_answer}
