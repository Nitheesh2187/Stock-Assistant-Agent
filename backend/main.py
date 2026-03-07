import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agent_manager import agent_manager
from backend.config import settings
from backend.store import ensure_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
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
from backend.routers import chat, stocks, watchlist  # noqa: E402

app.include_router(watchlist.router)
app.include_router(stocks.router)
app.include_router(chat.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "tools": [t.name for t in agent_manager.tools]}


@app.post("/api/session")
async def create_session():
    session_id = str(uuid.uuid4())
    ensure_session(session_id)
    return {"session_id": session_id}
