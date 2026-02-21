"""
Dynamic Feature Management Module

This module provides functionality for managing ML model features and making predictions.
It includes feature definitions and prediction tracking.

Components:
- schemas: SQLAlchemy ORM models for database tables
- models: Pydantic request/response schemas
- repositories: Data access layer for database operations
- services: Business logic for validation and predictions
- routes: API endpoint definitions

All API endpoints require user authentication.
"""

from backend.dynamic.routes import (
    features_router,
    predictions_router
)

__all__ = [
    "features_router",
    "predictions_router"
]
