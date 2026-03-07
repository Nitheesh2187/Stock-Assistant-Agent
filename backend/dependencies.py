from fastapi import Header, HTTPException, status

from backend.store import ensure_session


def get_session_id(x_session_id: str = Header(...)) -> str:
    """Extract and validate the X-Session-Id header."""
    if not x_session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-Session-Id header")
    return ensure_session(x_session_id)
