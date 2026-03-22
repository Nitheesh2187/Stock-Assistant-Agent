"""Session management — async PostgreSQL backed."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Session


async def ensure_session(db: AsyncSession, session_id: str) -> str:
    """Register a session if not already known and return its ID."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    if result.scalar_one_or_none() is None:
        db.add(Session(id=session_id))
        await db.commit()
    return session_id
