"""AgentState schema for LangGraph agentic workflows."""

from typing import Annotated, Sequence, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Clean shared memory for the customer session in LangGraph.

    Attributes:
        messages: Conversation history and recent messages, automatically appended using add_messages.
        customer_email: Optional customer email saved during the conversation.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    customer_email: Optional[str]
