"""
ANFIS model storage — works on both SQLite and PostgreSQL.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, LargeBinary, ForeignKey
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .compat import UUIDType, JSONType


class ANFISModel(Base):
    """ANFIS model storage"""
    __tablename__ = "anfis_models"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(20), nullable=False)           # 'size', 'iat'
    version = Column(Integer, default=1)
    trained_on = Column(DateTime(timezone=True), server_default=func.now())
    training_dataset = Column(String(255), nullable=True)     # Dataset name/path
    accuracy_metrics = Column(JSONType, nullable=True)        # Loss, discriminator accuracy
    model_weights = Column(LargeBinary, nullable=True)        # Serialized PyTorch state_dict
    is_active = Column(Boolean, default=False)
    created_by = Column(UUIDType, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<ANFISModel(name='{self.model_name}', type='{self.model_type}', active={self.is_active})>"
