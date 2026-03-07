from datetime import datetime
from pydantic import BaseModel


# ── Watchlist ─────────────────────────────────────────────────────────────────

class WatchlistAddRequest(BaseModel):
    symbol: str
    stock_name: str


class WatchlistItemResponse(BaseModel):
    id: str
    symbol: str
    stock_name: str
    added_at: str


class StockSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str
    type: str


# ── Chat ──────────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class MessageHistoryResponse(BaseModel):
    messages: list[MessageResponse]
    has_more: bool
