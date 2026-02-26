"""
Pydantic schemas for admin operations.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ Admin User Schemas ============

class AdminUserCreate(BaseModel):
    """Schema for creating admin user."""
    email: str
    password: str
    username: str
    is_admin: bool = True


class AdminUserOut(BaseModel):
    """Schema for admin user response."""
    id: int
    email: str
    username: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


# ============ Feature Management Schemas ============

class AdminFeatureCreate(BaseModel):
    """Schema for admin to create feature."""
    name: str
    label: str
    data_type: str  # boolean, float, int, string
    model_type: str  # land, house, rental
    required: bool = False
    active: bool = True


class AdminFeatureUpdate(BaseModel):
    """Schema for admin to update feature."""
    name: Optional[str] = None
    label: Optional[str] = None
    data_type: Optional[str] = None
    required: Optional[bool] = None
    active: Optional[bool] = None


class AdminFeatureOut(BaseModel):
    """Schema for feature response to admin."""
    id: int
    name: str
    label: str
    data_type: str
    model_type: str
    required: bool
    active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============ User Management Schemas ============

class AdminUserListOut(BaseModel):
    """Schema for returning user list to admin."""
    id: int
    email: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminDashboardStats(BaseModel):
    """Schema for admin dashboard statistics."""
    total_users: int
    total_features: int
    total_predictions: int
