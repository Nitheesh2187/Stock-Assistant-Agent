from datetime import datetime
from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str


# ── Watchlist ─────────────────────────────────────────────────────────────────

class WatchlistAddRequest(BaseModel):
    symbol: str
    stock_name: str


class WatchlistItemResponse(BaseModel):
    id: str
    symbol: str
    stock_name: str
    added_at: datetime

    class Config:
        from_attributes = True


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
    created_at: datetime

    class Config:
        from_attributes = True


class MessageHistoryResponse(BaseModel):
    messages: list[MessageResponse]
    has_more: bool
