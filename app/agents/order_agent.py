"""Order Agent service specializing in inventory stock checks and order placement."""

import json
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent

from sqlalchemy.orm import Session
from app.config import settings, logger
from app.tools.order_tools import SearchProductsTool, CheckInventoryTool, PlaceOrderTool


ORDER_AGENT_SYSTEM_PROMPT = (
    "You are the Order Agent for an Agentic Order Management System.\n"
    "Your responsibility is to assist customers with discovering products, checking stock, and placing new orders.\n\n"
    "Behavior Guidelines:\n"
    "- If the user provides a product name or description without a product_id, search the inventory catalog first to find matching products.\n"
    "- If search returns exactly 1 matching product, automatically use its `product_id` for checking stock and placing the order.\n"
    "- If search returns multiple products, present the matching options clearly to the user and ask them to select one.\n"
    "- If customer email is missing, ask the user to provide their email address before placing the order.\n"
    "- Always execute order placement when all details (product_id, quantity, customer_email) are confirmed.\n"
    "- Provide clear, concise, and helpful responses with the order details and confirmation."
)


from app.agents.llm_factory import get_llm


class OrderAgent:
    """Specialized Agent for handling order placement workflows using create_agent."""

    def __init__(self, db: Session):
        self.db = db
        self.tools = [
            SearchProductsTool(db=self.db),
            CheckInventoryTool(db=self.db),
            PlaceOrderTool(db=self.db),
        ]

        self._llm = get_llm(temperature=0.1)

        self.agent = create_agent(
            model=self._llm,
            tools=self.tools,
            system_prompt=ORDER_AGENT_SYSTEM_PROMPT,
        )

    def run(self, prompt: str, history: List[BaseMessage] = None) -> Dict[str, Any]:
        """Execute the Order Agent via create_agent harness.

        Args:
            prompt (str): Natural language customer request.
            history (List[BaseMessage]): Previous conversation history messages.

        Returns:
            Dict[str, Any]: Agent response dictionary with final answer string.
        """
        logger.info(f"Running Order Agent via create_agent for prompt: '{prompt}'")

        messages: List[BaseMessage] = list(history) if history else []
        messages.append(HumanMessage(content=prompt))

        result = self.agent.invoke({"messages": messages})
        result_messages = result.get("messages", [])

        final_answer = str(result_messages[-1].content) if result_messages else ""
        return {"answer": final_answer}


