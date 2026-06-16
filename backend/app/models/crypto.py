"""
Cryptographic key model — works on both SQLite and PostgreSQL.
"""
from sqlalchemy import Column, String, Boolean, DateTime, LargeBinary, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..database import Base
from .compat import UUIDType


class CryptoKey(Base):
    """Cryptographic key storage"""
    __tablename__ = "crypto_keys"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_type = Column(String(20), nullable=False)    # 'kem_public', 'kem_secret', 'sig_public', 'sig_secret'
    algorithm = Column(String(50), nullable=False)   # 'Kyber512', 'Dilithium2'
    key_data = Column(LargeBinary, nullable=False)   # Encrypted key material (Fernet)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # No unique constraint on user_id, key_type, and is_active to allow multiple inactive keys (history)

    def __repr__(self):
        return f"<CryptoKey(type='{self.key_type}', algorithm='{self.algorithm}')>"
