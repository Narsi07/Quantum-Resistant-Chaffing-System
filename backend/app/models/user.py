"""
User model
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base
from .compat import UUIDType


class UserRole(str, enum.Enum):
    """User roles"""
    ADMIN = "admin"
    ANALYST = "analyst"
    USER = "user"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"
