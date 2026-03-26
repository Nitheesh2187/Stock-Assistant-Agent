import sys
from pathlib import Path

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # API Keys
    GROQ_API_KEY: str = ""
    ALPHAVANTAGE_API_KEY: str = ""
    FIRECRAWL_API_KEY: str = ""

    # LLM
    LLM_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    LLM_TEMPERATURE: float = 0.6

    # Agent
    AGENT_MAX_ITERATIONS: int = 5
    EXECUTOR_TTL_SECONDS: int = 30 * 60  # 30 minutes
    MAX_STREAM_RETRIES: int = 2
    TOOL_CALL_RETRIES: int = 3
    TOOL_CALL_TIMEOUT: int = 30  # seconds

    # Circuit breaker — disable a tool after N consecutive failures
    CIRCUIT_BREAKER_THRESHOLD: int = 5   # failures before tripping
    CIRCUIT_BREAKER_COOLDOWN: int = 300  # seconds before re-enabling (5 min)

    SYSTEM_PROMPT: str = (
        "You are analyzing {symbol} ({stock_name}).\n"
        "You are a helpful stock market assistant with access to real-time stock data, "
        "financial analysis tools, and web scraping capabilities.\n\n"
        "You can help with:\n"
        "- Real-time stock quotes and price data\n"
        "- Company fundamentals and financial metrics\n"
        "- Latest stock news and market developments\n"
        "- Comprehensive stock analysis\n"
        "- Web scraping for additional research\n\n"
        "You provide information for educational and research purposes only.\n"
        "Never recommend buying, selling, or holding any specific stock.\n"
        "Always present data clearly and explain your reasoning."
    )

    REQUIRED_TOOLS: set[str] = {
        "get_stock_quote",
        "get_stock_fundamentals",
        "get_stock_news",
        "firecrawl_scrape",
    }

    # Database — set DATABASE_URL directly (e.g. Render), or use individual fields
    DATABASE_URL: str = ""
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "stock_assistant"

    @property
    def db_url(self) -> str:
        """Use DATABASE_URL if set, otherwise build from individual fields."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Render gives postgresql://, we need postgresql+asyncpg://
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # CORS (comma-separated in env, e.g. CORS_ORIGINS=https://myapp.onrender.com,http://localhost:5173)
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_ALL: bool = False  # Set to true in production if frontend is same-origin

    @property
    def mcp_servers(self) -> dict:
        """MCP server connection configs. Built as a property so FIRECRAWL_API_KEY is resolved."""
        return {
            "stock_tools": {
                "command": sys.executable,
                "args": ["-m", "stock_mcp.server"],
                "transport": "stdio",
            },
            "firecrawl-mcp": {
                "command": "npx",
                "args": ["-y", "firecrawl-mcp"],
                "env": {"FIRECRAWL_API_KEY": self.FIRECRAWL_API_KEY},
                "transport": "stdio",
            },
        }

    class Config:
        env_file = ".env"


settings = Settings()
