"""Orchestrator Agent specializing in multi-agent routing and coordination."""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain.agents import create_agent

from app.core.llm import get_llm
from app.prompts import INTENT_ROUTER_SYSTEM_PROMPT


class RouteDecision(BaseModel):
    """Input schema for routing the conversation to a specialist agent."""

    destination: Literal["order_node", "cancellation_node", "enquiry_node", "general_reply"] = Field(
        ...,
        description="The target destination node for the conversation based on user intent."
    )
    reply: Optional[str] = Field(
        default=None,
        description="Polite and helpful direct reply if the destination is 'general_reply'.",
    )


class OrchestratorAgent:
    """Specialized Agent for analyzing user intent and delegating to specialist agents."""

    def __init__(self):
        self._llm = get_llm(temperature=0.0)
        self.agent = create_agent(
            model=self._llm,
            response_format=RouteDecision,
            system_prompt=INTENT_ROUTER_SYSTEM_PROMPT,
        )


orchestrator_agent = OrchestratorAgent()

