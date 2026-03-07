"""In-memory session-scoped storage — no database, no persistence."""

import uuid

# session_id → True
sessions: dict[str, bool] = {}

# session_id → list[{id, symbol, stock_name, added_at}]
watchlists: dict[str, list[dict]] = {}

# (session_id, symbol) → {id, messages: list[{id, role, content, created_at}]}
conversations: dict[tuple[str, str], dict] = {}


def new_id() -> str:
    return str(uuid.uuid4())


def ensure_session(session_id: str) -> str:
    """Register a session if not already known and return it."""
    if session_id not in sessions:
        sessions[session_id] = True
        watchlists[session_id] = []
    return session_id
