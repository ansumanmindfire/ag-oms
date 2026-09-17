"""Order Agent specializing in inventory stock checks and order placement."""

from langchain.agents import create_agent

from app.tools.order_tools import (
    SearchProductsTool,
    CheckInventoryTool,
    PlaceOrderTool,
    SendOrderConfirmationEmailTool,
)
from app.core.llm import get_llm
from app.prompts import ORDER_AGENT_SYSTEM_PROMPT


class OrderAgent:
    """Specialized Agent for handling order placement workflows."""

    def __init__(self):
        self.tools = [
            SearchProductsTool(),
            CheckInventoryTool(),
            PlaceOrderTool(),
            SendOrderConfirmationEmailTool(),
        ]
        self._llm = get_llm(temperature=0.1)
        self.agent = create_agent(
            model=self._llm,
            tools=self.tools,
            system_prompt=ORDER_AGENT_SYSTEM_PROMPT,
        )


order_agent = OrderAgent()
