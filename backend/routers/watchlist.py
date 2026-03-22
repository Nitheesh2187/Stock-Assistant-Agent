from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_session_id
from backend.models import WatchlistItem
from backend.schemas import StockSearchResult, WatchlistAddRequest, WatchlistItemResponse
from backend.services.stock_service import search_stocks

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("/", response_model=list[WatchlistItemResponse])
async def list_watchlist(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.session_id == session_id)
        .order_by(WatchlistItem.added_at)
    )
    items = result.scalars().all()
    return [
        WatchlistItemResponse(
            id=item.id,
            symbol=item.symbol,
            stock_name=item.stock_name,
            added_at=item.added_at.isoformat(),
        )
        for item in items
    ]


@router.post("/", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    req: WatchlistAddRequest,
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    # Check for duplicate
    exists = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.session_id == session_id,
            WatchlistItem.symbol == req.symbol,
        )
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stock already in watchlist")

    item = WatchlistItem(session_id=session_id, symbol=req.symbol, stock_name=req.stock_name)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return WatchlistItemResponse(
        id=item.id,
        symbol=item.symbol,
        stock_name=item.stock_name,
        added_at=item.added_at.isoformat(),
    )


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    symbol: str,
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.session_id == session_id,
            WatchlistItem.symbol == symbol,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not in watchlist")
    await db.delete(item)
    await db.commit()


@router.get("/search", response_model=list[StockSearchResult])
async def search(q: str = Query(..., min_length=1)):
    results = await search_stocks(q)
    return [StockSearchResult(**r) for r in results]
