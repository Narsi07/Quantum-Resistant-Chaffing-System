"""
Alert model — works on both SQLite and PostgreSQL.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .compat import UUIDType


class Alert(Base):
    """Alert model"""
    __tablename__ = "alerts"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    session_id = Column(UUIDType, ForeignKey("traffic_sessions.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # 'high_overhead', 'decryption_failure', etc.
    severity = Column(String(20), nullable=False)     # info, warning, error, critical
    message = Column(Text, nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Alert(type='{self.alert_type}', severity='{self.severity}')>"
