"""
API routes for admin management.
Requires admin authentication.
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.auth.authentication import get_current_user
from backend.admin.schemas import (
    AdminFeatureCreate,
    AdminFeatureUpdate,
    AdminFeatureOut,
    AdminUserListOut,
    AdminDashboardStats
)
from backend.admin.services import (
    get_all_features_admin,
    get_features_by_model_type,
    get_feature_by_id,
    create_feature_admin,
    update_feature_admin,
    delete_feature_admin,
    get_all_users_admin,
    get_dashboard_stats
)


# Type aliases
Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]


def check_admin_role(current_user: Annotated[dict, Depends(get_current_user)]):
    """Middleware to check if user is admin."""
    # For now, we'll use a simple check based on email pattern
    # In production, you should have an is_admin field in the database
    admin_email = "admin@reva.com"
    if current_user.get("email") != admin_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# ============ Admin Dashboard Router ============

admin_router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_user)]
)


@admin_router.get("/stats", response_model=AdminDashboardStats)
def get_admin_stats(
    db: Database,
    current_user: Annotated[dict, Depends(check_admin_role)]
):
    """Get admin dashboard statistics."""
    stats = get_dashboard_stats(db)
    return AdminDashboardStats(**stats)


# ============ Admin Features Router ============

@admin_router.get("/features", response_model=List[AdminFeatureOut])
def list_all_features(
    db: Database,
    current_user: Annotated[dict, Depends(check_admin_role)],
    model_type: str = None
):
    """
    List all features. Optionally filter by model type.
    
    Args:
        model_type: Optional filter by model type (land, house, rental)
    """
    if model_type:
        features = get_features_by_model_type(db, model_type)
    else:
        features = get_all_features_admin(db)
    
    return features


@admin_router.get("/features/{feature_id}", response_model=AdminFeatureOut)
def get_feature_details(
    feature_id: int,
    db: Database,
    current_user: Annotated[dict, Depends(check_admin_role)]
):
    """Get details of a specific feature."""
    feature = get_feature_by_id(db, feature_id)
    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )
    return feature


@admin_router.post("/features", response_model=AdminFeatureOut)
def create_new_feature(
    feature: AdminFeatureCreate,
    db: Database,
    current_user: Annotated[dict, Depends(check_admin_role)]
):
    """
    Create a new feature definition.
    
    Args:
        feature: Feature creation data
    """
    try:
        created_feature = create_feature_admin(db, feature.dict())
        return created_feature
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@admin_router.put("/features/{feature_id}", response_model=AdminFeatureOut)
def update_feature(
    feature_id: int,
    feature_update: AdminFeatureUpdate,
    db: Database,
    current_user: Annotated[dict, Depends(check_admin_role)]
):
    """
    Update a feature definition.
    
    Args:
        feature_id: ID of feature to update
        feature_update: Updated feature data
    """
    updated_feature = update_feature_admin(db, feature_id, feature_update.dict(exclude_unset=True))
    if not updated_feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )
    return updated_feature


@admin_router.delete("/features/{feature_id}")
def delete_feature(
    feature_id: int,
    db: Database,
    current_user: Annotated[dict, Depends(check_admin_role)]
):
    """Delete a feature definition."""
    success = delete_feature_admin(db, feature_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )
    return {"message": "Feature deleted successfully"}


# ============ Admin Users Router ============

@admin_router.get("/users", response_model=List[AdminUserListOut])
def list_all_users(
    db: Database,
    current_user: Annotated[dict, Depends(check_admin_role)]
):
    """Get list of all users."""
    users = get_all_users_admin(db)
    return users
