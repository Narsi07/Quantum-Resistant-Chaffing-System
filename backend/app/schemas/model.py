"""
ANFIS model schemas
"""
from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime


class ModelUploadRequest(BaseModel):
    """Schema for model upload"""
    model_name: str
    model_type: str  # 'size' or 'iat'
    training_dataset: Optional[str] = None
    accuracy_metrics: Optional[dict] = None


class ANFISModelResponse(BaseModel):
    """Schema for ANFIS model response"""
    id: UUID4
    model_name: str
    model_type: str
    version: int
    trained_on: datetime
    training_dataset: Optional[str]
    accuracy_metrics: Optional[dict]
    is_active: bool
    created_by: Optional[UUID4]
    
    class Config:
        from_attributes = True
