import uuid
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from langchain.agents import create_agent

from app.config import logger
from app.core.llm import get_llm, extract_text_content
from app.graph.subgraphs import (
    order_subgraph,
    cancellation_subgraph,
    enquiry_subgraph,
)
from app.prompts import SUPERVISOR_SYSTEM_PROMPT
from app.graph.checkpointer import checkpointer


# Pydantic Input Schemas for Supervisor Tools

class CallOrderAgentInput(BaseModel):
    """Input schema for delegating tasks to the specialized Order Agent."""
    request: str = Field(
        ...,
        description="Detailed customer request for ordering products, purchasing items, checking stock availability, or inquiring about available product catalog."
    )


class CallCancellationAgentInput(BaseModel):
    """Input schema for delegating tasks to the specialized Cancellation Agent."""
    request: str = Field(
        ...,
        description="Detailed customer request for cancelling an existing order or verifying order cancellation status."
    )


class CallEnquiryAgentInput(BaseModel):
    """Input schema for delegating technical product spec questions to Enquiry Agent."""
    request: str = Field(
        ...,
        description="Detailed customer enquiry about product comparisons, side-by-side feature differences, technical specifications, smart features, Wi-Fi, battery life, display, noise ratings, or warranty."
    )


# BaseTool Subclasses wrapping the shared agent singletons

class CallOrderAgentTool(BaseTool):
    """Tool for delegating order placement, stock verification, product pricing, and inventory search tasks to OrderAgent."""

    name: str = "call_order_agent"
    description: str = (
        "Useful for purchasing products, placing orders, checking product stock, "
        "inquiring about available items in stock, or getting product prices. "
        "Delegates task to the specialized Order Agent."
    )
    args_schema: Type[BaseModel] = CallOrderAgentInput

    def _run(self, request: str) -> str:
        """Synchronous execution of OrderAgent call."""
        logger.info(f"Supervisor Tool Execution [call_order_agent]: request='{request}'")
        result = order_subgraph.invoke({"messages": [HumanMessage(content=request)]})
        return extract_text_content(result["messages"][-1].content)


class CallCancellationAgentTool(BaseTool):
    """Tool for delegating order cancellations, stock restoration, and refund verification tasks to CancellationAgent."""

    name: str = "call_cancellation_agent"
    description: str = (
        "Useful for cancelling existing customer orders or verifying order cancellation status. "
        "Delegates task to the specialized Cancellation Agent."
    )
    args_schema: Type[BaseModel] = CallCancellationAgentInput

    def _run(self, request: str) -> str:
        """Synchronous execution of CancellationAgent call."""
        logger.info(f"Supervisor Tool Execution [call_cancellation_agent]: request='{request}'")
        result = cancellation_subgraph.invoke({"messages": [HumanMessage(content=request)]})
        return extract_text_content(result["messages"][-1].content)


class CallEnquiryAgentTool(BaseTool):
    """Tool for delegating technical product specifications and warranty queries to EnquiryAgent."""

    name: str = "call_enquiry_agent"
    description: str = (
        "Useful for comparing products in the store, side-by-side feature comparisons, "
        "technical product specifications, smart features, Wi-Fi capabilities, battery life, "
        "display specs, noise levels, or warranty details. "
        "Delegates task to the specialized Enquiry Agent."
    )
    args_schema: Type[BaseModel] = CallEnquiryAgentInput

    def _run(self, request: str) -> str:
        """Synchronous execution of EnquiryAgent call."""
        logger.info(f"Supervisor Tool Execution [call_enquiry_agent]: request='{request}'")
        result = enquiry_subgraph.invoke({"messages": [HumanMessage(content=request)]})
        return extract_text_content(result["messages"][-1].content)


# Supervisor Agent Tools
supervisor_tools: List[BaseTool] = [
    CallOrderAgentTool(),
    CallCancellationAgentTool(),
    CallEnquiryAgentTool(),
]


class SupervisorAgent:
    """Supervisor Agent that orchestrates domain agents autonomously via ReAct tool calling.

    Uses SqliteSaver checkpointer for automatic multi-turn session persistence,
    identical to how the LangGraph StateGraph approach handles memory.
    """

    def __init__(self):
        self._llm = get_llm(temperature=0.0)
        self.agent = create_agent(
            model=self._llm,
            tools=supervisor_tools,
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
            checkpointer=checkpointer,
        )

    def run(
        self,
        prompt: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the Supervisor Agent pipeline.

        Args:
            prompt: Natural language customer request.
            session_id: Optional session ID for multi-turn tracking.

        Returns:
            Dict with 'session_id' and 'answer'.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        active_session_id = session_id.strip() if (session_id and session_id.strip()) else str(uuid.uuid4())
        logger.info(f"Running Supervisor Agent for session '{active_session_id}', prompt: '{prompt}'")

        # thread_id config enables the checkpointer to auto-load/save conversation history
        config = {"configurable": {"thread_id": active_session_id}}

        result = self.agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
        )
        result_messages = result.get("messages", [])

        answer_text = (
            extract_text_content(result_messages[-1].content)
            if result_messages
            else "No response generated."
        )

        return {
            "session_id": active_session_id,
            "answer": answer_text,
        }


supervisor_agent = SupervisorAgent()
