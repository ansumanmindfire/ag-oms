"""Master Supervisor Orchestrator Agent for multi-agent delegation using create_agent."""

from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain.agents import create_agent

from app.config import logger
from app.repositories import ChatRepository
from app.services.redis_service import redis_service
from app.agents.order_agent import OrderAgent
from app.agents.cancellation_agent import CancellationAgent
from app.agents.enquiry_agent import EnquiryAgent
from app.agents.llm_factory import get_llm


SUPERVISOR_SYSTEM_PROMPT = (
    "You are the Customer Support Assistant for our store.\n"
    "Your responsibility is to assist customers with product catalog inquiries, technical specifications, placing orders, checking stock, and handling cancellations.\n\n"
    "INTERNAL TOOLS (FOR YOUR USE ONLY):\n"
    "- Use `call_order_agent` for searching available products, checking inventory stock, or placing orders.\n"
    "- Use `call_cancellation_agent` for cancelling existing orders or verifying order cancellation status.\n"
    "- Use `call_enquiry_agent` for technical product specifications, smart features, display, battery life, or warranty details.\n\n"
    "CRITICAL CONTEXT RESOLUTION:\n"
    "- When delegating to internal tools (`call_order_agent`, `call_cancellation_agent`, `call_enquiry_agent`), you MUST resolve all references and pronouns from prior conversation turns (such as selected product names, product IDs, quantities, customer emails, or order IDs) into a self-contained, complete `request` parameter so the tool has all necessary facts to execute without needing prior turns.\n\n"
    "CRITICAL OUTPUT & DELIVERY RULES (STRICT):\n"
    "1. MANDATORY RESULT DELIVERY: When an internal tool executes and returns information (such as product names, prices, stock availability, specifications, or order confirmation), you MUST present those complete findings, prices, and details directly to the customer. NEVER reply with placeholders like 'let me check' when the tool has already provided the answer.\n"
    "2. UNIFIED PERSONA: Speak directly to the customer in a warm, professional, helpful first-person tone ('We have the following options available for you...').\n"
    "3. ZERO ARCHITECTURE LEAKS: NEVER mention internal agent names (such as 'Order Agent', 'Cancellation Agent', 'Supervisor Agent') or tool names (such as `call_order_agent`, `call_cancellation_agent`, `place_order`) to the customer.\n"
    "4. NATURAL MISSING-INFO REQUESTS: If required information is missing to complete an action (such as customer email, quantity, or order ID), ask the customer for it directly (e.g., 'Could you please provide your email address so I can place this order?')."
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

        # Memory Fetch: Fast Redis RAM check with SQLite fallback (Cache-Aside Pattern)
        langchain_history: List[BaseMessage] = []
        redis_msgs = redis_service.get_session_memory(active_session_id, limit=10)

        if redis_msgs:
            for msg in redis_msgs:
                if msg.get("sender") == "user":
                    langchain_history.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("sender") == "ai":
                    langchain_history.append(AIMessage(content=msg.get("content", "")))
        else:
            # Cache miss: fetch from SQLite and rehydrate Redis hot memory
            db_history = ChatRepository.get_history_messages(db, active_session_id, limit=10)
            for msg in db_history:
                if msg.sender == "user":
                    langchain_history.append(HumanMessage(content=msg.content))
                elif msg.sender == "ai":
                    langchain_history.append(AIMessage(content=msg.content))
            redis_service.rehydrate_session_memory(
                active_session_id,
                [{"sender": m.sender, "content": m.content} for m in db_history],
            )

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

        # Dual Write: Persist permanently in SQLite and update hot Redis memory
        try:
            ChatRepository.save_message(db, active_session_id, sender="user", content=prompt)
            ChatRepository.save_message(db, active_session_id, sender="ai", content=answer_text)
        except Exception as save_err:
            logger.error(f"Failed to persist chat turns to DB: {save_err}")

        redis_service.push_session_messages(active_session_id, prompt, answer_text)

        return {
            "session_id": active_session_id,
            "answer": answer_text,
        }



# Global Master Orchestrator Agent instance
master_orchestrator = MasterOrchestratorAgent()


