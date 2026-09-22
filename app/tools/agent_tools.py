"""Agent-as-a-Tool wrappers for delegating tasks to specialist subgraphs."""

from typing import Type, List
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool

from app.config import logger
from app.llm import extract_text_content

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
        from app.graph.subgraphs import order_subgraph

        logger.info(f"Agent Tool Execution [call_order_agent]: request='{request}'")
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
        from app.graph.subgraphs import cancellation_subgraph

        logger.info(f"Agent Tool Execution [call_cancellation_agent]: request='{request}'")
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
        from app.graph.subgraphs import enquiry_subgraph

        logger.info(f"Agent Tool Execution [call_enquiry_agent]: request='{request}'")
        result = enquiry_subgraph.invoke({"messages": [HumanMessage(content=request)]})
        logger.debug(result)
        return extract_text_content(result["messages"][-1].content)


# Exported list of all agent tools
supervisor_tools: List[BaseTool] = [
    CallOrderAgentTool(),
    CallCancellationAgentTool(),
    CallEnquiryAgentTool(),
]

