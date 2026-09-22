"""Streaming utility helpers for SSE token and event streaming."""

from app.constants import TOOL_STATUS_MESSAGES


def get_tool_status_message(tool_name: str) -> str:
    """Return customer-friendly status text for executing agent tool."""
    return TOOL_STATUS_MESSAGES.get(tool_name, f"Delegating to {tool_name}...")
