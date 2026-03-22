"""Async chat/conversation helpers — PostgreSQL backed."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import Conversation, Message


async def get_or_create_conversation(db: AsyncSession, session_id: str, symbol: str) -> Conversation:
    """Get existing conversation for session+symbol, or create a new one."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.session_id == session_id,
            Conversation.symbol == symbol,
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        conv = Conversation(session_id=session_id, symbol=symbol)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
    return conv


async def add_message(db: AsyncSession, session_id: str, symbol: str, role: str, content: str) -> Message:
    """Append a message to the conversation (creates conversation if needed)."""
    conv = await get_or_create_conversation(db, session_id, symbol)
    msg = Message(conversation_id=conv.id, role=role, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(
    db: AsyncSession, session_id: str, symbol: str, limit: int = 50, before: str | None = None
) -> tuple[list[dict], bool]:
    """Return (messages_list, has_more) for pagination."""
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.session_id == session_id,
            Conversation.symbol == symbol,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if conv is None:
        return [], False

    query = select(Message).where(Message.conversation_id == conv.id)

    if before:
        # Get the created_at of the "before" message for cursor pagination
        before_result = await db.execute(select(Message.created_at).where(Message.id == before))
        before_ts = before_result.scalar_one_or_none()
        if before_ts is not None:
            query = query.where(Message.created_at < before_ts)

    query = query.order_by(Message.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    messages = rows[:limit]
    messages.reverse()  # oldest first

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ], has_more


async def get_conversation_history(db: AsyncSession, session_id: str, symbol: str) -> list[dict]:
    """Full history as list of {role, content} dicts for agent memory."""
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.session_id == session_id,
            Conversation.symbol == symbol,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if conv is None:
        return []

    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conv.id,
            Message.role.in_(["user", "assistant"]),
        )
        .order_by(Message.created_at)
    )
    return [{"role": m.role, "content": m.content} for m in result.scalars().all()]


async def delete_conversation(db: AsyncSession, session_id: str, symbol: str) -> bool:
    """Delete a conversation and its messages. Returns True if it existed."""
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.session_id == session_id,
            Conversation.symbol == symbol,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if conv is None:
        return False

    await db.delete(conv)
    await db.commit()
    return True
