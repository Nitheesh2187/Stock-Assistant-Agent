import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agent_manager import agent_manager
from backend.config import settings
from backend.database import init_db
from backend.routers import auth, chat, stocks, watchlist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    await init_db()
    await agent_manager.initialize()
    logger.info("Startup complete.")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(title="Stock Assistant API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(watchlist.router)
app.include_router(stocks.router)
app.include_router(chat.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "tools": [t.name for t in agent_manager.tools]}
