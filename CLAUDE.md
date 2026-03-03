# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered stock market assistant with a FastAPI backend and React + Tailwind frontend. Uses Groq (qwen/qwen3-32b) as the LLM, LangChain for agent orchestration, and two MCP servers for stock data (Alpha Vantage) and web scraping (Firecrawl). Features JWT auth, per-stock WebSocket chat with streaming, a watchlist, TradingView charts, and dark mode.

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
- **FastAPI** app with async SQLite (SQLAlchemy + aiosqlite)
- **Routers**: `auth.py` (register/login/refresh/me), `watchlist.py` (CRUD + Yahoo Finance search), `stocks.py` (quote/fundamentals/news via MCP tools), `chat.py` (REST history + WebSocket streaming)
- **Agent**: LangChain `AgentExecutor` with `ConversationBufferMemory`, streaming via `astream_events`
- **Auth**: JWT access tokens (30 min) + refresh tokens (7 days), bcrypt passwords
- **DB**: SQLite at `backend/stock_assistant.db` (path resolved from `backend/config.py`)

### Frontend (`frontend/`)
- **Vite + React 18 + Tailwind CSS v4**
- **3-column dashboard**: watchlist sidebar (280px) | center content (flex) | chat panel (360px)
- **State**: AuthContext (user/tokens), StockContext (selectedSymbol), local hooks for everything else
- **WebSocket chat**: token streaming, tool start/end indicators, message history via REST
- **TradingView**: script-injected Advanced Chart widget, symbol mapping (.NS → NSE:, .BO → BSE:)

### MCP Server Integration

Two MCP servers launched as stdio subprocesses:

1. **stock_tools** (`python -m stock_mcp.server`) — Provides: `get_stock_quote`, `get_stock_fundamentals`, `get_stock_news`, `get_stock_analysis`. Data from Alpha Vantage.
2. **firecrawl-mcp** (`npx -y firecrawl-mcp`) — Provides: `firecrawl_scrape`. Requires Node.js/npm.

## Environment Variables

Required in `.env` at project root:
- `GROQ_API_KEY` — Groq API access
- `ALPHAVANTAGE_API_KEY` — Stock data via Alpha Vantage
- `FIRECRAWL_API_KEY` — Web scraping via Firecrawl
- `JWT_SECRET_KEY` — JWT signing (defaults to dev secret)

## Python Version

Requires Python >=3.10.
