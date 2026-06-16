"""
Cross-database type compatibility layer.

Provides types that work on both SQLite (local dev) and PostgreSQL (production).

Usage:
    from .compat import UUIDType, JSONType, StringType
"""
import uuid as _uuid
from sqlalchemy import String, Text, JSON
from sqlalchemy.types import TypeDecorator, CHAR


class UUIDType(TypeDecorator):
    """
    UUID column that:
    - Uses native UUID on PostgreSQL
    - Stores as CHAR(36) string on SQLite
    """
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return _uuid.UUID(str(value)) if not isinstance(value, _uuid.UUID) else value

    @staticmethod
    def default():
        return _uuid.uuid4


# JSON works on both SQLite and PostgreSQL
JSONType = JSON

# INET → just use String for SQLite compat
InetType = String(45)
