from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.store import ensure_session


async def get_session_id(
    x_session_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Extract and validate the X-Session-Id header."""
    if not x_session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-Session-Id header")
    return await ensure_session(db, x_session_id)
