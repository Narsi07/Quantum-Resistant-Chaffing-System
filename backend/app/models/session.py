"""
Traffic session and packet log models
"""
from sqlalchemy import Column, String, BigInteger, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..database import Base
from .compat import UUIDType, JSONType


class TrafficSession(Base):
    """Traffic session model"""
    __tablename__ = "traffic_sessions"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType, ForeignKey("users.id"), nullable=True)
    session_name = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    total_packets = Column(BigInteger, default=0)
    real_packets = Column(BigInteger, default=0)
    dummy_packets = Column(BigInteger, default=0)
    total_bytes = Column(BigInteger, default=0)
    config = Column(JSONType, nullable=True)  # Session configuration
    status = Column(String(20), default='active')  # active, stopped, archived
    
    def __repr__(self):
        return f"<TrafficSession(name='{self.session_name}', status='{self.status}')>"


class PacketLog(Base):
    """Packet log model (time-series data)"""
    __tablename__ = "packet_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(UUIDType, ForeignKey("traffic_sessions.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    packet_type = Column(String(10), nullable=False)  # 'real', 'dummy'
    size_bytes = Column(Integer, nullable=False)
    iat_ms = Column(Float, nullable=True)  # Inter-arrival time in milliseconds
    path_id = Column(Integer, nullable=True)  # Multipath routing path
    encrypted = Column(Boolean, default=True)
    extra_meta = Column(JSONType, nullable=True)  # Additional packet metadata
    
    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<PacketLog(type='{self.packet_type}', size={self.size_bytes})>"
