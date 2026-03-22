import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent_manager import agent_manager
from backend.database import get_db, async_session
from backend.dependencies import get_session_id
from backend.schemas import MessageHistoryResponse, MessageResponse
from backend.services.chat_service import (
    delete_conversation,
    get_messages,
)
from backend.store import ensure_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── WebSocket streaming chat ─────────────────────────────────────────────────

@router.websocket("/{symbol}/ws")
async def websocket_chat(websocket: WebSocket, symbol: str, session_id: str = Query(...)):
    # WebSocket endpoints can't use Depends for DB sessions,
    # so we create one manually.
    async with async_session() as db:
        session_id = await ensure_session(db, session_id)

    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") != "message" or not data.get("content", "").strip():
                continue

            user_message = data["content"].strip()

            # Each message gets its own DB session
            async with async_session() as db:
                async for event in agent_manager.chat_stream(
                    db=db,
                    session_id=session_id,
                    symbol=symbol,
                    user_message=user_message,
                ):
                    if event["type"] == "token":
                        await websocket.send_text(json.dumps({"type": "token", "content": event["content"]}))

                    elif event["type"] == "tool_start":
                        await websocket.send_text(json.dumps({"type": "tool_start", "tool_name": event["tool_name"]}))

                    elif event["type"] == "tool_end":
                        await websocket.send_text(json.dumps({"type": "tool_end", "tool_name": event["tool_name"]}))

                    elif event["type"] == "done":
                        await websocket.send_text(json.dumps({"type": "done"}))

                    elif event["type"] == "error":
                        await websocket.send_text(json.dumps({"type": "error", "content": event["content"]}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}, symbol={symbol}")
    except Exception:
        logger.exception("WebSocket error")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except Exception:
            pass


# ── REST: Message history ────────────────────────────────────────────────────

@router.get("/{symbol}/messages", response_model=MessageHistoryResponse)
async def get_message_history(
    symbol: str,
    limit: int = Query(50, ge=1, le=100),
    before: str | None = Query(None),
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    messages, has_more = await get_messages(db, session_id, symbol, limit, before)
    return MessageHistoryResponse(
        messages=[MessageResponse(**m) for m in messages],
        has_more=has_more,
    )


# ── REST: Delete conversation ────────────────────────────────────────────────

@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    symbol: str,
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_conversation(db, session_id, symbol)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No conversation found")
    agent_manager.remove_executor(session_id, symbol)
