from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.dependencies import get_session_id
from backend.schemas import StockSearchResult, WatchlistAddRequest, WatchlistItemResponse
from backend.services.stock_service import search_stocks
from backend.store import new_id, watchlists

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("/", response_model=list[WatchlistItemResponse])
async def list_watchlist(session_id: str = Depends(get_session_id)):
    return watchlists.get(session_id, [])


@router.post("/", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    req: WatchlistAddRequest,
    session_id: str = Depends(get_session_id),
):
    items = watchlists.setdefault(session_id, [])

    if any(item["symbol"] == req.symbol for item in items):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Stock already in watchlist")

    entry = {
        "id": new_id(),
        "symbol": req.symbol,
        "stock_name": req.stock_name,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(entry)
    return entry


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    symbol: str,
    session_id: str = Depends(get_session_id),
):
    items = watchlists.get(session_id, [])
    for i, item in enumerate(items):
        if item["symbol"] == symbol:
            items.pop(i)
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not in watchlist")


@router.get("/search", response_model=list[StockSearchResult])
async def search(q: str = Query(..., min_length=1)):
    results = await search_stocks(q)
    return [StockSearchResult(**r) for r in results]
