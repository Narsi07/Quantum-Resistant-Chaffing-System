"""
Session schemas
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    """Schema for creating a new session"""
    session_name: Optional[str] = None
    config: Optional[dict] = None


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: UUID4
    user_id: Optional[UUID4]
    session_name: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    total_packets: int
    real_packets: int
    dummy_packets: int
    total_bytes: int
    config: Optional[dict]
    status: str
    
    class Config:
        from_attributes = True


class PacketLogResponse(BaseModel):
    """Schema for packet log response"""
    id: int
    session_id: UUID4
    timestamp: datetime
    packet_type: str
    size_bytes: int
    iat_ms: Optional[float]
    path_id: Optional[int]
    encrypted: bool
    extra_meta: Optional[dict]
    
    class Config:
        from_attributes = True
