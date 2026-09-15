"""Order Agent service specializing in inventory stock checks and order placement."""

import json
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain.agents import create_agent

from sqlalchemy.orm import Session
from app.config import settings, logger
from app.tools.order_tools import (
    SearchProductsTool,
    CheckInventoryTool,
    PlaceOrderTool,
    SendOrderConfirmationEmailTool,
)
from app.agents.llm_factory import get_llm, extract_text_content
from app.prompts import ORDER_AGENT_SYSTEM_PROMPT


class OrderAgent:
    """Specialized Agent for handling order placement workflows using create_agent."""

    def __init__(self, db: Session):
        self.db = db
        self.tools = [
            SearchProductsTool(db=self.db),
            CheckInventoryTool(db=self.db),
            PlaceOrderTool(db=self.db),
            SendOrderConfirmationEmailTool(db=self.db),
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

        final_answer = extract_text_content(result_messages[-1].content) if result_messages else ""
        return {"answer": final_answer}


