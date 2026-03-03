import json
import logging

import httpx

from backend.agent_manager import agent_manager

logger = logging.getLogger(__name__)

YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"


async def get_stock_quote(symbol: str) -> dict:
    result = await agent_manager.call_tool("get_stock_quote", {"symbol": symbol})
    if isinstance(result, str):
        return json.loads(result)
    return result


async def get_stock_fundamentals(symbol: str) -> dict:
    result = await agent_manager.call_tool("get_stock_fundamentals", {"ticker": symbol})
    if isinstance(result, str):
        return json.loads(result)
    return result


async def get_stock_news(symbol: str, stock_name: str, limit: int = 10) -> dict:
    result = await agent_manager.call_tool(
        "get_stock_news",
        {"ticker": symbol, "stock_name": stock_name, "max_items": limit},
    )
    if isinstance(result, str):
        return json.loads(result)
    return result


async def search_stocks(query: str) -> list[dict]:
    """Search stocks via Yahoo Finance autocomplete API."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                YAHOO_SEARCH_URL,
                params={"q": query, "quotesCount": 10, "newsCount": 0},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5.0,
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for quote in data.get("quotes", []):
            results.append({
                "symbol": quote.get("symbol", ""),
                "name": quote.get("shortname") or quote.get("longname", ""),
                "exchange": quote.get("exchange", ""),
                "type": quote.get("quoteType", ""),
            })
        return results

    except Exception:
        logger.exception("Yahoo Finance search failed")
        return []
