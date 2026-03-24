import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent_manager import agent_manager
from backend.config import settings
from backend.database import close_db, get_db, init_db
from backend.store import ensure_session

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

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
    # Shutdown — cleanly terminate MCP subprocesses and DB pool
    await agent_manager.shutdown()
    await close_db()


app = FastAPI(title="Stock Assistant API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ALLOW_ALL else settings.CORS_ORIGINS,
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
async def create_session(db: AsyncSession = Depends(get_db)):
    session_id = str(uuid.uuid4())
    await ensure_session(db, session_id)
    return {"session_id": session_id}


# ── Serve frontend static files (production) ────────────────────────────────

if FRONTEND_DIR.is_dir():
    # Serve JS/CSS/images from /assets
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    # Catch-all: serve index.html for any non-API route (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")
