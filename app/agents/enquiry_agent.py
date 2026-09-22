"""Enquiry Agent specializing in product specification search and vector RAG retrieval."""

from langchain.agents import create_agent

from app.tools.enquiry_tools import SearchProductSpecsTool
from app.llm import get_llm
from app.constants import LLM_TEMPERATURE
from app.prompts import ENQUIRY_AGENT_SYSTEM_PROMPT


class EnquiryAgent:
    """Specialized Agent for handling product specification enquiry workflows."""

    def __init__(self):
        self.tools = [SearchProductSpecsTool()]
        self._llm = get_llm(temperature=LLM_TEMPERATURE)
        self.agent = create_agent(
            model=self._llm,
            tools=self.tools,
            system_prompt=ENQUIRY_AGENT_SYSTEM_PROMPT,
        )


enquiry_agent = EnquiryAgent()
