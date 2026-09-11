"""Master Supervisor Orchestrator Agent for multi-agent delegation using create_agent."""

from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain.agents import create_agent

from app.config import logger
from app.repositories import ChatRepository
from app.agents.order_agent import OrderAgent
from app.agents.cancellation_agent import CancellationAgent
from app.agents.enquiry_agent import EnquiryAgent
from app.agents.llm_factory import get_llm


SUPERVISOR_SYSTEM_PROMPT = (
    "You are the Master Supervisor Agent for an Agentic Order Management System.\n"
    "Your responsibility is to assist customers by orchestrating and delegating tasks to specialized worker agents:\n"
    "- Use `call_order_agent` for ordering products, purchasing items, checking product stock, or inquiring about available products.\n"
    "- Use `call_cancellation_agent` for cancelling existing orders or verifying order cancellation status.\n"
    "- Use `call_enquiry_agent` for product technical specifications, features, display, battery life, or warranty details.\n\n"
    "CRITICAL INSTRUCTIONS:\n"
    "- Analyze the customer request and conversation history carefully.\n"
    "- Execute the appropriate worker tool(s).\n"
    "- Always include the complete, detailed findings and response from the worker agent in your final answer to the user."
)


# Pydantic Schemas for Supervisor Tools

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
        description="Detailed customer enquiry about product technical specifications, smart features, Wi-Fi, battery life, display, noise ratings, or warranty."
    )


# BaseTool Subclasses for Supervisor Tools

class CallOrderAgentTool(BaseTool):
    """Tool for delegating order placement, stock verification, product pricing, and inventory search tasks to OrderAgent."""

    name: str = "call_order_agent"
    description: str = (
        "Useful for purchasing products, placing orders, checking product stock, "
        "inquiring about available items in stock, or getting product prices. "
        "Delegates task to the specialized Order Agent."
    )
    args_schema: Type[BaseModel] = CallOrderAgentInput
    db: Any = Field(default=None, exclude=True)

    def _run(self, request: str) -> str:
        """Synchronous execution of OrderAgent call."""
        logger.info(f"Supervisor Tool Execution [call_order_agent]: request='{request}'")
        agent = OrderAgent(db=self.db)
        res = agent.run(prompt=request)
        return res.get("answer", "")


class CallCancellationAgentTool(BaseTool):
    """Tool for delegating order cancellations, stock restoration, and refund verification tasks to CancellationAgent."""

    name: str = "call_cancellation_agent"
    description: str = (
        "Useful for cancelling existing customer orders or verifying order cancellation status. "
        "Delegates task to the specialized Cancellation Agent."
    )
    args_schema: Type[BaseModel] = CallCancellationAgentInput
    db: Any = Field(default=None, exclude=True)

    def _run(self, request: str) -> str:
        """Synchronous execution of CancellationAgent call."""
        logger.info(f"Supervisor Tool Execution [call_cancellation_agent]: request='{request}'")
        agent = CancellationAgent(db=self.db)
        res = agent.run(prompt=request)
        return res.get("answer", "")


class CallEnquiryAgentTool(BaseTool):
    """Tool for delegating technical product specifications and warranty queries to EnquiryAgent."""

    name: str = "call_enquiry_agent"
    description: str = (
        "Useful for technical product specifications, smart features, Wi-Fi capabilities, "
        "battery life, display specs, noise levels, or warranty details. "
        "Delegates task to the specialized Enquiry Agent."
    )
    args_schema: Type[BaseModel] = CallEnquiryAgentInput

    def _run(self, request: str) -> str:
        """Synchronous execution of EnquiryAgent call."""
        logger.info(f"Supervisor Tool Execution [call_enquiry_agent]: request='{request}'")
        agent = EnquiryAgent()
        res = agent.run(prompt=request)
        return res.get("answer", "")


def get_supervisor_tools(db: Session) -> List[BaseTool]:
    """Generates supervisor worker BaseTools bound to the active database session."""
    return [
        CallOrderAgentTool(db=db),
        CallCancellationAgentTool(db=db),
        CallEnquiryAgentTool(),
    ]


class MasterOrchestratorAgent:
    """Master Supervisor Agent that orchestrates worker agents using create_agent."""

    def _get_llm(self) -> Any:
        """Initializes and returns configured LLM instance via get_llm factory."""
        return get_llm(temperature=0.0)

    def run(
        self,
        prompt: str,
        db: Session,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main Supervisor Pipeline:
        1. Fetch/Create chat session.
        2. Rehydrate past messages from DB.
        3. Execute Supervisor Agent via create_agent with sub-agent worker tools.
        4. Persist user prompt & AI answer to DB.
        5. Return complete structured response payload.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        # Fetch or Create Session
        if session_id:
            session_rec = ChatRepository.get_session_by_id(db, session_id)
            if not session_rec:
                logger.warning(f"Session ID '{session_id}' not found. Creating new session.")
                session_rec = ChatRepository.create_session(db, session_name="Order Chat Session")
        else:
            session_rec = ChatRepository.create_session(db, session_name="Order Chat Session")

        active_session_id = session_rec.id

        # Rehydrate Conversation History
        db_history = ChatRepository.get_history_messages(db, active_session_id, limit=10)
        langchain_history: List[BaseMessage] = []
        for msg in db_history:
            if msg.sender == "user":
                langchain_history.append(HumanMessage(content=msg.content))
            elif msg.sender == "ai":
                langchain_history.append(AIMessage(content=msg.content))

        # Build Supervisor Tools and Supervisor Agent via create_agent
        supervisor_tools = get_supervisor_tools(db=db)
        supervisor_agent = create_agent(
            model=self._get_llm(),
            tools=supervisor_tools,
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
        )

        messages: List[BaseMessage] = list(langchain_history)
        messages.append(HumanMessage(content=prompt))

        logger.info(f"Running Master Supervisor Agent via create_agent for prompt: '{prompt}'")
        result = supervisor_agent.invoke({"messages": messages})
        result_messages = result.get("messages", [])

        # Extract AIMessage content
        answer_text = str(result_messages[-1].content) if result_messages else "No response generated."

        # Print step-by-step agent decision using pretty_print()
        for msg in result_messages:
            msg.pretty_print()

        try:
            ChatRepository.save_message(db, active_session_id, sender="user", content=prompt)
            ChatRepository.save_message(db, active_session_id, sender="ai", content=answer_text)
        except Exception as save_err:
            logger.error(f"Failed to persist chat turns to DB: {save_err}")

        return {
            "session_id": active_session_id,
            "answer": answer_text,
        }



# Global Master Orchestrator Agent instance
master_orchestrator = MasterOrchestratorAgent()


