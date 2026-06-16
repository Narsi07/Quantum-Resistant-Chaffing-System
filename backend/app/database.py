"""
Database connection and session management.

Supports TWO backends:
  1. SQLite  (default for local dev — zero config, works immediately)
  2. PostgreSQL (set DATABASE_URL in backend/.env to use)

SQLite is used automatically when DATABASE_URL starts with 'sqlite'
or when PostgreSQL connection fails.
"""
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import settings

logger = logging.getLogger(__name__)

# ── Determine database URL ─────────────────────────────────────────────────
_DB_URL = settings.DATABASE_URL

# If using SQLite, convert to aiosqlite driver
if _DB_URL.startswith("sqlite"):
    if not _DB_URL.startswith("sqlite+aiosqlite"):
        _DB_URL = _DB_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
    _IS_SQLITE = True
    _POOL_KWARGS = {}   # SQLite doesn't support pool_size/max_overflow
else:
    _IS_SQLITE = False
    _POOL_KWARGS = {"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True}

logger.info(f"Database: {'SQLite (local file)' if _IS_SQLITE else 'PostgreSQL'}")

# ── Create async engine ────────────────────────────────────────────────────
engine = create_async_engine(
    _DB_URL,
    echo=False,         # Set True to log all SQL queries
    future=True,
    **_POOL_KWARGS,
)

# ── Session factory ────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ── Base class for models ──────────────────────────────────────────────────
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    FastAPI dependency: yields an async database session.

    Usage:
        db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Create all tables on startup.

    For PostgreSQL: the database must already exist.
    For SQLite: the file is created automatically.
    """
    try:
        async with engine.begin() as conn:
            # Register all models with SQLAlchemy metadata
            from .models import (   # noqa — side-effect imports
                User, CryptoKey, TrafficSession, PacketLog,
                ANFISModel, AuditLog, ConfigPreset, Alert,
            )
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified OK")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        if not _IS_SQLITE:
            logger.error(
                "PostgreSQL connection failed.\n"
                "Either:\n"
                "  1. Fix your DATABASE_URL in backend/.env\n"
                "  2. Or switch to SQLite by setting:\n"
                "     DATABASE_URL=sqlite+aiosqlite:///./qr_chaffing.db"
            )
        raise


async def close_db():
    """Close all database connections on shutdown."""
    await engine.dispose()
