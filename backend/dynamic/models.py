from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional


# ============ Feature Definition Schemas ============

class FeatureCreate(BaseModel):
    """Schema for creating a new feature."""
    name: str
    label: str
    data_type: str  # boolean, float, int, string
    model_type: str  # land, house, rental
    required: bool = False
    active: bool = True


class FeatureOut(BaseModel):
    """Schema for feature response."""
    id: int
    name: str
    label: str
    data_type: str
    model_type: str
    required: bool
    active: bool

    model_config = ConfigDict(from_attributes=True)


class FeatureUpdate(BaseModel):
    """Schema for updating a feature."""
    name: Optional[str] = None
    label: Optional[str] = None
    data_type: Optional[str] = None
    required: Optional[bool] = None
    active: Optional[bool] = None


# ============ Prediction Schemas ============

class PredictionRequest(BaseModel):
    """Schema for prediction request."""
    features: Dict[str, Any]


class PredictionResponse(BaseModel):
    """Schema for prediction response."""
    predicted_value: float
    model_type: str


class PredictionRecordOut(BaseModel):
    """Schema for prediction record response."""
    id: int
    user_id: int
    model_type: str
    predicted_value: str

    model_config = ConfigDict(from_attributes=True)
