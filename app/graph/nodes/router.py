from typing import Literal, Optional
from pydantic import BaseModel, Field
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import SystemMessage, AIMessage

from app.config import logger
from app.graph.state import AgentState
from app.core.llm import get_llm
from app.prompts import INTENT_ROUTER_SYSTEM_PROMPT


class IntentClassification(BaseModel):
    target: Literal["order_node", "cancellation_node", "enquiry_node", "general_reply"] = Field(
        description="The target specialist node to route the conversation to"
    )
    reply: Optional[str] = Field(
        default=None,
        description="A polite and helpful direct reply if the target is 'general_reply'",
    )


# Instantiate router LLM with structured output schema
router_llm = get_llm(temperature=0.0).with_structured_output(IntentClassification)


def classify_intent(
    state: AgentState,
) -> Command[Literal["order_node", "cancellation_node", "enquiry_node", END]]:
    """Classifies customer intent from conversation state and routes directly via Command

    Args:
        state: Current graph state containing conversation messages and metadata

    Returns:
        Command: either specifying the next node to execute or ending
    """
    messages = list(state.get("messages", []))
    logger.info("Classifying customer intent in LangGraph workflow...")

    prompt_messages = [SystemMessage(content=INTENT_ROUTER_SYSTEM_PROMPT)] + messages
    decision: IntentClassification = router_llm.invoke(prompt_messages)
    logger.info(f"Intent classified: target='{decision.target}'")

    # If the intent of the user is general (not task specific)
    if decision.target not in [
        "order_node",
        "cancellation_node",
        "enquiry_node",
    ]:
        greeting_text = (
            decision.reply
            or "Hi! I am your AI assistant for the Order Management System. Tell me how can I assist you?"
        )
        return Command(
            update={"messages": [AIMessage(content=greeting_text)]},
            goto=END,
        )

    # Route immediately to the chosen specialist node
    return Command(goto=decision.target)
