# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered stock market assistant with a FastAPI backend and React + Tailwind frontend. Uses Groq as the LLM, LangChain for agent orchestration, and two MCP servers for stock data (Yahoo Finance / Alpha Vantage) and web scraping (Firecrawl). Features session-based auth, per-stock WebSocket chat with streaming, a watchlist, TradingView charts, and dark mode.

## Commands

### Run locally (two terminals)
```bash
make backend    # FastAPI on http://localhost:8000
make frontend   # Vite on http://localhost:5173
```

### Install dependencies
```bash
make install    # pip + npm
```

### Run with Docker
```bash
docker-compose up --build        # builds and starts (port 8051)
docker-compose up -d             # detached mode
docker-compose down              # stop
```

## Architecture

### Backend (`backend/`)
- **FastAPI** app with in-memory storage (`store.py` — sessions, watchlists, conversations as Python dicts)
- **Routers**: `watchlist.py` (CRUD + Yahoo Finance search), `stocks.py` (quote/fundamentals/news via MCP tools), `chat.py` (REST history + WebSocket streaming)
- **Auth**: Session-based via `X-Session-Id` header (no JWT currently)
- **AgentManager** (`agent_manager.py`): Singleton that manages:
  - Persistent MCP sessions via `AsyncExitStack` (subprocesses live for the app's lifetime)
  - Per-conversation `CachedExecutor` instances (executor + memory + lock) with 30-min TTL eviction
  - `chat_stream()` owns the full lifecycle: saves user message, runs agent, saves assistant response
  - Graceful shutdown via `shutdown()` called from the FastAPI lifespan handler

### Agent Architecture
- LangChain `AgentExecutor` with `ConversationBufferMemory`, streaming via `astream_events`
- Executors are cached per `(session_id, symbol)` — first message builds the executor, subsequent messages reuse it
- On cold start (server restart or TTL eviction), memory is rebuilt from stored conversation history
- Per-conversation `asyncio.Lock` prevents concurrent agent runs on the same conversation

### Frontend (`frontend/`)
- **Vite + React 18 + Tailwind CSS v4**
- **3-column dashboard**: watchlist sidebar (280px) | center content (flex) | chat panel (360px)
- **State**: StockContext (selectedSymbol), local hooks for everything else
- **WebSocket chat**: token streaming, tool start/end indicators, message history via REST
- **TradingView**: script-injected Advanced Chart widget, symbol mapping (.NS → NSE:, .BO → BSE:)

### MCP Server Integration

Two MCP servers launched as persistent stdio subprocesses at startup (managed by `AsyncExitStack`):

1. **stock_tools** (`python -m stock_mcp.server`) — Provides: `get_stock_quote`, `get_stock_fundamentals`, `get_stock_news`. Data from Yahoo Finance with Alpha Vantage fallback.
2. **firecrawl-mcp** (`npx -y firecrawl-mcp`) — Provides: `firecrawl_scrape`. Requires Node.js/npm.

Sessions are persistent (not per-tool-call), and gracefully closed on app shutdown.

## Environment Variables

Required in `.env` at project root:
- `GROQ_API_KEY` — Groq API access
- `ALPHAVANTAGE_API_KEY` — Stock data fallback via Alpha Vantage
- `FIRECRAWL_API_KEY` — Web scraping via Firecrawl

## Python Version

Requires Python >=3.10.
