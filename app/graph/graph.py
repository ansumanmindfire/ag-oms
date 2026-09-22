from typing import Optional, Dict, Any, Generator
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk

from app.config import logger
from app.graph.state import AgentState
from app.graph.checkpointer import checkpointer
from app.graph.nodes import orchestrator_node
from app.tools.agent_tools import supervisor_tools
from app.llm import extract_text_content
from app.utils.session import resolve_session_id
from app.utils.streaming import get_tool_status_message


def create_oms_graph():
    """Build and compile the OMS StateGraph using the Agent-as-a-Tool supervisor pattern."""
    workflow = StateGraph(AgentState)

    # Add orchestrator node and tools node
    workflow.add_node("orchestrator_node", orchestrator_node)
    workflow.add_node("tools", ToolNode(supervisor_tools))

    # Entry edge
    workflow.add_edge(START, "orchestrator_node")

    # Conditional edge as per the orchestrator
    workflow.add_conditional_edges(
        "orchestrator_node",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END,
        }
    )

    # Return from tools back to orchestrator for final synthesis
    workflow.add_edge("tools", "orchestrator_node")

    # Compile with checkpointer for automatic multi-turn state persistence
    return workflow.compile(checkpointer=checkpointer)


oms_graph = create_oms_graph()

def run_oms_graph(
    prompt: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Runs the OMS StateGraph for a user prompt, managing session ID and conversation turns.

    Args:
        prompt: Customer's incoming text request.
        session_id: Optional chat session ID from the client.

    Returns:
        Dict with 'session_id' and 'answer'.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    active_session_id = resolve_session_id(session_id)
    logger.info(f"Executing LangGraph OMS workflow for session '{active_session_id}', prompt: '{prompt}'")

    config = {"configurable": {"thread_id": active_session_id}}

    result = oms_graph.invoke(
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


def stream_oms_graph(
    prompt: str,
    session_id: Optional[str] = None,
) -> Generator[Dict[str, Any], None, None]:
    """Streams the OMS StateGraph execution yielding status and token chunks via SSE.

    Args:
        prompt: Customer's incoming text request.
        session_id: Optional chat session ID from the client.

    Yields:
        Dict event items with 'type': 'session' | 'status' | 'token'.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    active_session_id = resolve_session_id(session_id)
    logger.info(f"Streaming LangGraph OMS workflow for session '{active_session_id}', prompt: '{prompt}'")

    config = {"configurable": {"thread_id": active_session_id}}
    yield {"type": "session", "session_id": active_session_id}

    for mode, payload in oms_graph.stream(
        {"messages": [HumanMessage(content=prompt)]},
        config=config,
        stream_mode=["updates", "messages"],
    ):
        if mode == "updates" and isinstance(payload, dict):
            if "orchestrator_node" in payload:
                msgs = payload["orchestrator_node"].get("messages", [])
                if msgs and hasattr(msgs[-1], "tool_calls") and msgs[-1].tool_calls:
                    for tc in msgs[-1].tool_calls:
                        yield {"type": "status", "content": get_tool_status_message(tc.get("name"))}
            elif "tools" in payload:
                yield {"type": "status", "content": "Agent completed task"}

        elif mode == "messages":
            chunk = payload[0]
            if isinstance(chunk, (AIMessage, AIMessageChunk)):
                text = extract_text_content(getattr(chunk, "content", ""))
                if text:
                    yield {"type": "token", "content": text}

