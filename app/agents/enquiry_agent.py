"""Enquiry Agent service specializing in product specification search and vector RAG retrieval."""

from typing import Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.agents import create_agent

from app.config import settings, logger
from app.tools.enquiry_tools import SearchProductSpecsTool
from app.agents.llm_factory import get_llm


ENQUIRY_AGENT_SYSTEM_PROMPT = (
    "You are the Enquiry Agent for an Agentic Order Management System.\n"
    "Your responsibility is to assist customers with product technical specifications, smart features, Wi-Fi capabilities, energy ratings, noise levels, and warranty details.\n\n"
    "Behavior Guidelines:\n"
    "- Always use `search_product_specs(query)` to retrieve specification context from Qdrant Vector DB.\n"
    "- Base your answers strictly on the retrieved specification text snippets.\n"
    "- Summarize features, technical specs, and warranty details in a polite, structured, and easy-to-read format.\n"
    "- If no specification documents match, inform the customer politely that specification PDFs can be uploaded to enrich the knowledge base."
)


class EnquiryAgent:
    """Specialized Agent for handling product specification enquiry workflows using create_agent."""

    def __init__(self):
        self.tools = [SearchProductSpecsTool()]
        self._llm = get_llm(temperature=0.1)

        self.agent = create_agent(
            model=self._llm,
            tools=self.tools,
            system_prompt=ENQUIRY_AGENT_SYSTEM_PROMPT,
        )

    def run(self, prompt: str, history: List[BaseMessage] = None) -> Dict[str, Any]:
        """Execute the Enquiry Agent via create_agent harness.

        Args:
            prompt (str): Natural language customer request.
            history (List[BaseMessage]): Previous conversation history.

        Returns:
            Dict[str, Any]: Agent response dictionary with final answer string.
        """
        logger.info(f"Running Enquiry Agent via create_agent for prompt: '{prompt}'")

        messages: List[BaseMessage] = list(history) if history else []
        messages.append(HumanMessage(content=prompt))

        result = self.agent.invoke({"messages": messages})
        result_messages = result.get("messages", [])

        final_answer = str(result_messages[-1].content) if result_messages else ""
        return {"answer": final_answer}
