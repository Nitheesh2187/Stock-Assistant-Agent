from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Conversation, Message


async def get_or_create_conversation(db: AsyncSession, user_id: str, symbol: str) -> Conversation:
    """Get existing conversation for user+symbol, or create a new one."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.symbol == symbol,
        )
    )
    conv = result.scalar_one_or_none()

    if not conv:
        conv = Conversation(user_id=user_id, symbol=symbol)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    return conv


async def add_message(db: AsyncSession, conversation_id: str, role: str, content: str) -> Message:
    """Add a message to a conversation and update the conversation's updated_at."""
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)

    # Update conversation timestamp
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one()
    conv.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(
    db: AsyncSession,
    conversation_id: str,
    limit: int = 50,
    before: str | None = None,
) -> tuple[list[Message], bool]:
    """Get paginated messages for a conversation.

    Returns:
        Tuple of (messages, has_more).
    """
    query = select(Message).where(Message.conversation_id == conversation_id)

    if before:
        # Get the created_at of the cursor message
        cursor_result = await db.execute(select(Message.created_at).where(Message.id == before))
        cursor_time = cursor_result.scalar_one_or_none()
        if cursor_time:
            query = query.where(Message.created_at < cursor_time)

    query = query.order_by(Message.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    messages = list(result.scalars().all())

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Return in chronological order
    messages.reverse()
    return messages, has_more


async def get_conversation_history(db: AsyncSession, conversation_id: str) -> list[dict]:
    """Get full conversation history as list of dicts for agent memory."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return [
        {"role": msg.role, "content": msg.content}
        for msg in result.scalars().all()
        if msg.role in ("user", "assistant")
    ]


async def delete_conversation(db: AsyncSession, user_id: str, symbol: str) -> bool:
    """Delete a conversation and all its messages for a user+symbol."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.symbol == symbol,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return False

    await db.delete(conv)
    await db.commit()
    return True
