"""
SQLAlchemy models used by the admin module.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime

from backend.database.database import Base


class ModelRegistry(Base):
    """
    Stores metadata for deployable ML models managed by admins.
    Only one model per model_type should be active at a time.
    """

    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    model_type = Column(String, nullable=False, index=True)  # land, house, rental
    version = Column(String, nullable=False, default="v1")
    deployed_endpoint = Column(String, nullable=False)
    artifact_url = Column(String, nullable=True)
    performance_notes = Column(String, nullable=True)

    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    r2_score = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)

    is_active = Column(Boolean, default=False, index=True)
    uploaded_by_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
