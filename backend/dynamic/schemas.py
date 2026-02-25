"""
SQLAlchemy ORM models for the dynamic feature management system.
These define the database tables for features and prediction records.
"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.database import Base


# ============ Feature Definition Model ============

class FeatureDefinition(Base):
    """
    Stores feature definitions for different ML models.
    Features define the input parameters required for model predictions.
    """
    __tablename__ = "feature_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    label = Column(String, nullable=False)
    data_type = Column(String, nullable=False)  # boolean, float, int, string
    model_type = Column(String, nullable=False, index=True)  # land, house, rental
    required = Column(Boolean, default=False)
    active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============ Prediction Record Model ============

class PredictionRecord(Base):
    """
    Stores historical prediction records for audit and analytics.
    Links predictions to users for tracking.
    """
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_type = Column(String, nullable=False, index=True)
    features = Column(JSON, nullable=False)
    predicted_value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
