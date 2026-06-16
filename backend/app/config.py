"""
Configuration management using Pydantic Settings.
Reads from backend/.env (absolute path — works regardless of cwd).
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

# Always resolve .env relative to this file's directory (backend/app/)
_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


class Settings(BaseSettings):
    """Application settings — loaded from backend/.env"""

    # Application
    APP_NAME: str = "Quantum-Resistant Chaffing API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database — default is SQLite (zero config)
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./qr_chaffing.db",
        description="Database URL. SQLite (default) or postgresql+asyncpg://..."
    )

    # Security
    SECRET_KEY: str = Field(
        default="56b821a66b6d48076cfde7788ba71a6364289f5904735f8602cc1f112e80e4136",
        description="JWT signing key"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS — allow all for local dev (auth is JWT-based)
    CORS_ORIGINS: list[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Fernet key for encrypting stored crypto keys in DB
    DB_ENCRYPTION_KEY: Optional[str] = Field(
        default="aEvR_TgHpDKQ94y38ctYzDWCoeiT1YgSt1dHXP_inzY=",
        description="Fernet key for DB encryption"
    )

    model_config = {
        "env_file": _ENV_FILE,
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


# Singleton
settings = Settings()
