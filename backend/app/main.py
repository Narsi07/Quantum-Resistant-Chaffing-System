"""
Main FastAPI application — serves the full system on ONE port.

Single URL: http://localhost:8000
  - / and /app  → HTML Frontend (index.html)
  - /api/...    → REST API
  - /api/docs   → Swagger UI
  - /api/engine/stream/{id} → WebSocket
"""
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db, close_db
from .api import auth_router, sessions_router, crypto_router, engine_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Frontend directory is at project_root/frontend/
# main.py lives at project_root/backend/app/main.py
# So project root = 2 levels up from this file
_FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Quantum-Resistant Chaffing API...")
    await init_db()
    logger.info("Database initialized OK")
    logger.info(f"System ready at: http://localhost:8000")
    logger.info(f"API docs at:     http://localhost:8000/api/docs")
    yield
    logger.info("Shutting down...")
    await close_db()


# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Quantum-Resistant Chaffing System API

Post-Quantum Metadata Obfuscation Layer using Neuro-Fuzzy Traffic Synthesis.

### Quick Start
1. Open **http://localhost:8000** in your browser
2. Register an account, then login
3. Create a session and start the obfuscation engine
    """,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS (allow same-origin and dev origins) ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Safe since auth is JWT-based
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging ────────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    ms = (time.time() - start) * 1000
    if not request.url.path.startswith("/static"):
        logger.debug(f"{request.method} {request.url.path} -> {response.status_code} ({ms:.0f}ms)")
    return response


# ── API Routers ────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(crypto_router)
app.include_router(engine_router)


# ── Serve Frontend Static Files ────────────────────────────────────────────
if os.path.isdir(_FRONTEND_DIR):
    # Serve CSS, JS, images etc. under /static/
    app.mount("/static", StaticFiles(directory=_FRONTEND_DIR), name="static")
    logger.info(f"Frontend directory found: {_FRONTEND_DIR}")
else:
    logger.warning(f"Frontend directory not found at {_FRONTEND_DIR}")


# ── Root → serve index.html ────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the HTML frontend at the root URL."""
    index_path = os.path.join(_FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse(
        "<h2>Frontend not found.</h2><p>Run from project root.</p>",
        status_code=404,
    )


# ── Health & Root API ──────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check."""
    try:
        import oqs  # noqa
        pq_mode = "real (liboqs)"
    except ImportError:
        pq_mode = "simulation"

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "pq_mode": pq_mode,
        "frontend": "http://localhost:8000",
        "api_docs": "http://localhost:8000/api/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
