"""
Configuration preset model — works on both SQLite and PostgreSQL.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .compat import UUIDType, JSONType


class ConfigPreset(Base):
    """Configuration preset model"""
    __tablename__ = "config_presets"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    preset_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    config_data = Column(JSONType, nullable=False)   # Full configuration object
    is_default = Column(Boolean, default=False)
    created_by = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ConfigPreset(name='{self.preset_name}', default={self.is_default})>"
