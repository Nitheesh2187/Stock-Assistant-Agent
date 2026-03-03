import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent_manager import agent_manager
from backend.database import async_session, get_db
from backend.dependencies import get_current_user
from backend.models import Conversation, User
from backend.schemas import MessageHistoryResponse, MessageResponse
from backend.services.auth_service import decode_token
from backend.services.chat_service import (
    add_message,
    delete_conversation,
    get_conversation_history,
    get_messages,
    get_or_create_conversation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── WebSocket auth helper ────────────────────────────────────────────────────

async def ws_authenticate(token: str) -> User | None:
    """Authenticate a WebSocket connection via JWT token query param."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


# ── WebSocket streaming chat ─────────────────────────────────────────────────

@router.websocket("/{symbol}/ws")
async def websocket_chat(websocket: WebSocket, symbol: str, token: str = Query(...)):
    user = await ws_authenticate(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") != "message" or not data.get("content", "").strip():
                continue

            user_message = data["content"].strip()

            # Get or create conversation and save user message
            async with async_session() as db:
                conv = await get_or_create_conversation(db, user.id, symbol)
                conversation_id = conv.id
                await add_message(db, conversation_id, "user", user_message)
                history = await get_conversation_history(db, conversation_id)

            # Derive stock_name from symbol (strip .NS/.BO suffix as fallback)
            stock_name = symbol.split(".")[0] if "." in symbol else symbol

            # Stream response
            full_response = ""
            async for event in agent_manager.chat_stream(
                conversation_id=conversation_id,
                user_message=user_message,
                symbol=symbol,
                stock_name=stock_name,
                history=history[:-1],  # exclude the just-added user message (agent gets it as input)
            ):
                if event["type"] == "token":
                    full_response = event.get("full_response", full_response)
                    await websocket.send_text(json.dumps({"type": "token", "content": event["content"]}))

                elif event["type"] == "tool_start":
                    await websocket.send_text(json.dumps({"type": "tool_start", "tool_name": event["tool_name"]}))

                elif event["type"] == "tool_end":
                    await websocket.send_text(json.dumps({"type": "tool_end", "tool_name": event["tool_name"]}))

                elif event["type"] == "done":
                    full_response = event.get("full_response", full_response)
                    # Save assistant response to DB
                    if full_response:
                        async with async_session() as db:
                            await add_message(db, conversation_id, "assistant", full_response)
                    await websocket.send_text(json.dumps({"type": "done"}))

                elif event["type"] == "error":
                    # Save error to DB
                    async with async_session() as db:
                        await add_message(db, conversation_id, "error", event["content"])
                    await websocket.send_text(json.dumps({"type": "error", "content": event["content"]}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user.id}, symbol={symbol}")
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_id == user.id,
            Conversation.symbol == symbol,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return MessageHistoryResponse(messages=[], has_more=False)

    messages, has_more = await get_messages(db, conv.id, limit, before)
    return MessageHistoryResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        has_more=has_more,
    )


# ── REST: Delete conversation ────────────────────────────────────────────────

@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    symbol: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_conversation(db, user.id, symbol)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No conversation found")
    agent_manager.remove_lock(f"{user.id}_{symbol}")
