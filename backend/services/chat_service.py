"""In-memory chat/conversation helpers."""

from datetime import datetime, timezone

from backend.store import conversations, new_id


def get_or_create_conversation(session_id: str, symbol: str) -> dict:
    """Get existing conversation for session+symbol, or create a new one."""
    key = (session_id, symbol)
    if key not in conversations:
        conversations[key] = {"id": new_id(), "messages": []}
    return conversations[key]


def add_message(session_id: str, symbol: str, role: str, content: str) -> dict:
    """Append a message to the conversation."""
    conv = get_or_create_conversation(session_id, symbol)
    msg = {
        "id": new_id(),
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    conv["messages"].append(msg)
    return msg


def get_messages(session_id: str, symbol: str, limit: int = 50, before: str | None = None):
    """Return (messages_list, has_more) for pagination."""
    conv = conversations.get((session_id, symbol))
    if not conv:
        return [], False

    msgs = conv["messages"]

    if before:
        idx = next((i for i, m in enumerate(msgs) if m["id"] == before), None)
        if idx is not None:
            msgs = msgs[:idx]

    has_more = len(msgs) > limit
    result = msgs[-limit:] if has_more else msgs
    return result, has_more


def get_conversation_history(session_id: str, symbol: str) -> list[dict]:
    """Full history as list of {role, content} dicts for agent memory."""
    conv = conversations.get((session_id, symbol))
    if not conv:
        return []
    return [
        {"role": m["role"], "content": m["content"]}
        for m in conv["messages"]
        if m["role"] in ("user", "assistant")
    ]


def delete_conversation(session_id: str, symbol: str) -> bool:
    """Delete a conversation. Returns True if it existed."""
    key = (session_id, symbol)
    if key in conversations:
        del conversations[key]
        return True
    return False
