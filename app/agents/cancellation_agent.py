"""Cancellation Agent specializing in order cancellations and inventory restoration."""

from langchain.agents import create_agent

from app.tools.cancellation_tools import CancelOrderTool
from app.core.llm import get_llm
from app.prompts import CANCELLATION_AGENT_SYSTEM_PROMPT


class CancellationAgent:
    """Specialized Agent for handling order cancellation workflows."""

    def __init__(self):
        self.tools = [CancelOrderTool()]
        self._llm = get_llm(temperature=0.1)
        self.agent = create_agent(
            model=self._llm,
            tools=self.tools,
            system_prompt=CANCELLATION_AGENT_SYSTEM_PROMPT,
        )


cancellation_agent = CancellationAgent()
