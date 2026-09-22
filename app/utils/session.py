"""Session ID resolution utility."""

import uuid
from typing import Optional


def resolve_session_id(session_id: Optional[str] = None) -> str:
    """
    If session_id is provided and non-blank, returns it stripped.
    Otherwise generates a new UUID4 string.

    Args:
        session_id: Optional session ID from the client.

    Returns:
        A non-empty session ID string.
    """
    if session_id and session_id.strip():
        return session_id.strip()
    return str(uuid.uuid4())
