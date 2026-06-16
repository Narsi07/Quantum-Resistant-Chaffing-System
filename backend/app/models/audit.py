"""
Audit log model — works on both SQLite and PostgreSQL.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .compat import UUIDType, JSONType, InetType


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # 'login', 'key_generated', 'session_started', etc.
    event_data = Column(JSONType, nullable=True)
    ip_address = Column(InetType, nullable=True)   # String(45) on SQLite, INET on PG
    severity = Column(String(20), default='info')  # debug, info, warning, error, critical

    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_event_type', 'event_type'),
    )

    def __repr__(self):
        return f"<AuditLog(event='{self.event_type}', severity='{self.severity}')>"
