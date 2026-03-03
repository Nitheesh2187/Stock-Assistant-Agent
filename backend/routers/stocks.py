from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_current_user
from backend.models import User
from backend.services import stock_service

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/{symbol}/quote")
async def quote(symbol: str, _: User = Depends(get_current_user)):
    return await stock_service.get_stock_quote(symbol)


@router.get("/{symbol}/fundamentals")
async def fundamentals(symbol: str, _: User = Depends(get_current_user)):
    return await stock_service.get_stock_fundamentals(symbol)


@router.get("/{symbol}/news")
async def news(
    symbol: str,
    stock_name: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    _: User = Depends(get_current_user),
):
    return await stock_service.get_stock_news(symbol, stock_name, limit)
