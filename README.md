# Stock Assistance Agent

AI-powered stock market assistant built with FastAPI, React, LangChain, and MCP (Model Context Protocol) servers. Provides real-time stock quotes, fundamental analysis, market news, and web scraping through an interactive chat interface with streaming responses.

## Features

- **Real-time Stock Quotes**: Current prices, daily range, volume via Yahoo Finance with Alpha Vantage fallback
- **Fundamental Analysis**: P/E ratios, financials, balance sheet, cash flow, ESG data
- **Market News**: Aggregated from Yahoo Finance and Google News RSS
- **Web Scraping**: Extract data from financial websites using Firecrawl
- **Streaming Chat**: Per-stock WebSocket chat with token streaming and tool call indicators
- **Watchlist**: Add/remove stocks, search via Yahoo Finance autocomplete
- **TradingView Charts**: Embedded Advanced Chart widget with NSE/BSE symbol mapping
- **Dark Mode**: Full dark mode support

## Architecture

```
React + Tailwind ◄──── WebSocket / REST ────► FastAPI Backend
                                                    │
                                              AgentManager
                                           (cached executors,
                                            persistent MCP sessions)
                                                    │
                                      ┌─────────────┴─────────────┐
                                      │                           │
                               stock_mcp server          firecrawl-mcp server
                              (Yahoo Finance,            (npx subprocess)
                               Alpha Vantage)
```

### Key Design Decisions

- **Persistent MCP sessions**: Subprocesses start once at boot via `AsyncExitStack`, not per tool call. Gracefully terminated on shutdown.
- **Cached agent executors**: `AgentExecutor` + `ConversationBufferMemory` cached per `(session_id, symbol)` with 30-min TTL. Cold starts rebuild memory from stored history.
- **Per-conversation locking**: `asyncio.Lock` per conversation prevents concurrent agent runs corrupting shared memory.
- **Self-contained `chat_stream()`**: Owns the full message lifecycle (save user message → run agent → save assistant response).

## Prerequisites

- Python 3.10+
- Node.js (for Firecrawl MCP server)
- Docker and Docker Compose (for containerized deployment)

## Required API Keys

1. **GROQ_API_KEY**: Get from [Groq](https://console.groq.com/keys)
2. **ALPHAVANTAGE_API_KEY**: Get from [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (fallback data source)
3. **FIRECRAWL_API_KEY**: Get from [Firecrawl](https://firecrawl.dev/)

## Installation & Setup

### Option 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nitheesh2187/Stock-Assistant-Agent.git
   cd stock-assistance-agent
   ```

2. **Install dependencies**
   ```bash
   make install    # installs pip + npm dependencies
   ```

   Or manually:
   ```bash
   pip install -r requirements.txt
   pip install git+https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git
   cd frontend && npm install
   ```

3. **Set up environment variables**

   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ALPHAVANTAGE_API_KEY=your_alphavantage_api_key_here
   FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   ```

4. **Run the application** (two terminals)
   ```bash
   make backend    # FastAPI on http://localhost:8000
   make frontend   # Vite on http://localhost:5173
   ```

### Option 2: Docker Deployment

1. **Clone and set up `.env`** (same as above)

2. **Build and run**
   ```bash
   docker-compose up --build     # http://localhost:8051
   docker-compose up -d          # detached mode
   docker-compose down           # stop
   ```

## Project Structure

```
stock-assistance-agent/
├── backend/
│   ├── main.py              # FastAPI app, lifespan (startup/shutdown)
│   ├── agent_manager.py     # AgentManager singleton (MCP sessions, executor cache, chat_stream)
│   ├── config.py            # Settings (API keys, LLM config, CORS)
│   ├── store.py             # In-memory storage (sessions, watchlists, conversations)
│   ├── dependencies.py      # FastAPI dependencies (session ID extraction)
│   ├── schemas.py           # Pydantic models
│   ├── routers/
│   │   ├── chat.py          # WebSocket streaming + REST message history
│   │   ├── stocks.py        # Stock quote/fundamentals/news endpoints
│   │   └── watchlist.py     # Watchlist CRUD + stock search
│   └── services/
│       ├── chat_service.py  # Conversation CRUD helpers
│       └── stock_service.py # MCP tool call wrappers + Yahoo search
├── frontend/                # React + Vite + Tailwind CSS v4
├── Dockerfile
├── docker-compose.yaml
├── Makefile
├── requirements.txt
└── .env                     # API keys (not committed)
```

## MCP Server Configuration

Two MCP servers run as persistent stdio subprocesses:

| Server | Command | Tools | Data Sources |
|--------|---------|-------|-------------|
| stock_tools | `python -m stock_mcp.server` | `get_stock_quote`, `get_stock_fundamentals`, `get_stock_news` | Yahoo Finance, Alpha Vantage |
| firecrawl-mcp | `npx -y firecrawl-mcp` | `firecrawl_scrape` | Firecrawl API |

## Usage Examples

- "What is the current price of Reliance Industries?"
- "Show me the fundamentals for TCS (TCS.NS)"
- "Get the latest news about Infosys stock"
- "Compare fundamentals of ICICI Bank vs HDFC Bank"
- "What are the P/E ratios for IT sector stocks?"

## Troubleshooting

1. **MCP Server Connection Failed**: Ensure all API keys are set in `.env`, verify Node.js is installed for Firecrawl
2. **Rate Limit Errors**: Alpha Vantage free tier has 25 requests/day. Yahoo Finance is the primary source.
3. **Docker Issues**: Ensure Docker and Docker Compose are installed, check that required ports are available

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Related Resources

- [Stock Analysis MCP Server](https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [Alpha Vantage API](https://www.alphavantage.co/documentation/)
- [Firecrawl Documentation](https://docs.firecrawl.dev/)
- [Groq Documentation](https://console.groq.com/docs)
