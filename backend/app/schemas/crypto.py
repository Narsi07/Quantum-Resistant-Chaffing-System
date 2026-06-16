"""
Crypto schemas
"""
from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime


class KeyGenerateRequest(BaseModel):
    """Schema for key generation request"""
    algorithm: str = "Kyber512"  # or Dilithium2


class CryptoKeyResponse(BaseModel):
    """Schema for crypto key response"""
    id: UUID4
    key_type: str
    algorithm: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True
