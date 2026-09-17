"""SQLite checkpointer singleton for multi-turn persistence across workflows."""

import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

from app.config import settings

# Ensure parent folder (/data) exists
checkpoint_path = Path(settings.CHECKPOINT_DB_PATH)
checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

# Persistent SQLite checkpointer for multi-turn session persistence
db_connection = sqlite3.connect(str(checkpoint_path), check_same_thread=False)
checkpointer = SqliteSaver(db_connection)
