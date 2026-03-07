import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from backend.agent_manager import agent_manager
from backend.dependencies import get_session_id
from backend.schemas import MessageHistoryResponse, MessageResponse
from backend.services.chat_service import (
    add_message,
    delete_conversation,
    get_conversation_history,
    get_messages,
    get_or_create_conversation,
)
from backend.store import ensure_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── WebSocket streaming chat ─────────────────────────────────────────────────

@router.websocket("/{symbol}/ws")
async def websocket_chat(websocket: WebSocket, symbol: str, session_id: str = Query(...)):
    session_id = ensure_session(session_id)

    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") != "message" or not data.get("content", "").strip():
                continue

            user_message = data["content"].strip()

            conv = get_or_create_conversation(session_id, symbol)
            conversation_id = conv["id"]
            add_message(session_id, symbol, "user", user_message)
            history = get_conversation_history(session_id, symbol)

            stock_name = symbol.split(".")[0] if "." in symbol else symbol

            full_response = ""
            async for event in agent_manager.chat_stream(
                conversation_id=conversation_id,
                user_message=user_message,
                symbol=symbol,
                stock_name=stock_name,
                history=history[:-1],
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
                    if full_response:
                        add_message(session_id, symbol, "assistant", full_response)
                    await websocket.send_text(json.dumps({"type": "done"}))

                elif event["type"] == "error":
                    add_message(session_id, symbol, "error", event["content"])
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
):
    messages, has_more = get_messages(session_id, symbol, limit, before)
    return MessageHistoryResponse(
        messages=[MessageResponse(**m) for m in messages],
        has_more=has_more,
    )


# ── REST: Delete conversation ────────────────────────────────────────────────

@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(
    symbol: str,
    session_id: str = Depends(get_session_id),
):
    deleted = delete_conversation(session_id, symbol)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No conversation found")
    agent_manager.remove_lock(f"{session_id}_{symbol}")
