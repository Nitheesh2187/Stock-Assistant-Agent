from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_session_id
from backend.services import stock_service

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/{symbol}/quote")
async def quote(symbol: str, _: str = Depends(get_session_id)):
    return await stock_service.get_stock_quote(symbol)


@router.get("/{symbol}/fundamentals")
async def fundamentals(symbol: str, _: str = Depends(get_session_id)):
    return await stock_service.get_stock_fundamentals(symbol)


@router.get("/{symbol}/news")
async def news(
    symbol: str,
    stock_name: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    _: str = Depends(get_session_id),
):
    return await stock_service.get_stock_news(symbol, stock_name, limit)
