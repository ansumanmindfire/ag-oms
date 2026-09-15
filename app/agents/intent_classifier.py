"""Intent Classifier node for LangGraph routing using Command(goto=...)."""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import SystemMessage, AIMessage

from app.config import logger
from app.agents.state import AgentState
from app.agents.llm_factory import get_llm

INTENT_ROUTER_SYSTEM_PROMPT = (
    "You are the Intent Routing Classifier for an ecommerce Order Management System.\n"
    "Your responsibility is to analyze the full conversation history and classify which specialized node "
    "should handle the customer's latest request.\n\n"
    "Target destinations:\n"
    "- 'order_node': Use for browsing available products, checking inventory stock, product pricing inquiries, "
    "reviewing order summaries, modifying order quantities, or confirming/placing a purchase.\n"
    "- 'cancellation_node': Use for cancelling existing orders, verifying order cancellation status, providing Order ID/email to cancel, "
    "or confirming order cancellations.\n"
    "- 'enquiry_node': Use for technical product specifications, smart capabilities, Wi-Fi features, battery life, "
    "display specs, noise ratings, dimensions, warranty terms, or side-by-side product comparisons.\n"
    "- 'general_reply': Use for general greetings ('hi', 'hello'), asking what you can do, or general pleasantries.\n"
)


class IntentClassification(BaseModel):
    """Structured classification decision for graph routing."""

    target: Literal["order_node", "cancellation_node", "enquiry_node", "general_reply"] = Field(
        description="The target specialist node to route the conversation to."
    )
    reply: Optional[str] = Field(
        default=None,
        description="A polite and helpful direct reply if the target is 'general_reply' (e.g. greetings or clarifying capabilities).",
    )


def classify_intent(
    state: AgentState,
) -> Command[Literal["order_node", "cancellation_node", "enquiry_node", END]]:
    """LangGraph node: classifies customer intent from state messages and routes directly via Command(goto=...)."""
    messages = list(state.get("messages", []))
    logger.info("Classifying customer intent in LangGraph workflow...")

    llm = get_llm(temperature=0.0).with_structured_output(IntentClassification)
    prompt_messages = [SystemMessage(content=INTENT_ROUTER_SYSTEM_PROMPT)] + messages

    decision: IntentClassification = llm.invoke(prompt_messages)
    logger.info(f"Intent classified: target='{decision.target}'")

    # If the user is just saying hello or asking general questions, reply directly and end the turn
    if decision.target == "general_reply" or decision.target not in [
        "order_node",
        "cancellation_node",
        "enquiry_node",
    ]:
        greeting_text = decision.reply
        return Command(
            update={"messages": [AIMessage(content=greeting_text)]},
            goto=END,
        )

    # Route immediately to the chosen specialist node
    return Command(goto=decision.target)
