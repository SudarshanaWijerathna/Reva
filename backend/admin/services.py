"""
Service layer for admin operations.
Handles business logic for admin features and user management.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.dynamic.schemas import FeatureDefinition, PredictionRecord
from backend.database.schemas import UserModel


# ============ Feature Management Services ============

def get_all_features_admin(db: Session) -> List[FeatureDefinition]:
    """Get all feature definitions (admin view)."""
    return db.query(FeatureDefinition).all()


def get_features_by_model_type(db: Session, model_type: str) -> List[FeatureDefinition]:
    """Get all features for a specific model type."""
    return db.query(FeatureDefinition)\
        .filter(FeatureDefinition.model_type == model_type)\
        .all()


def get_feature_by_id(db: Session, feature_id: int) -> FeatureDefinition:
    """Get a specific feature by ID."""
    return db.query(FeatureDefinition)\
        .filter(FeatureDefinition.id == feature_id)\
        .first()


def create_feature_admin(db: Session, feature_data: Dict[str, Any]) -> FeatureDefinition:
    """Create a new feature definition (admin)."""
    new_feature = FeatureDefinition(**feature_data)
    db.add(new_feature)
    db.commit()
    db.refresh(new_feature)
    return new_feature


def update_feature_admin(db: Session, feature_id: int, feature_data: Dict[str, Any]) -> FeatureDefinition:
    """Update a feature definition (admin)."""
    db_feature = get_feature_by_id(db, feature_id)
    if db_feature:
        for key, value in feature_data.items():
            if value is not None:
                setattr(db_feature, key, value)
        db.commit()
        db.refresh(db_feature)
    return db_feature


def delete_feature_admin(db: Session, feature_id: int) -> bool:
    """Delete a feature definition (admin)."""
    db_feature = get_feature_by_id(db, feature_id)
    if db_feature:
        db.delete(db_feature)
        db.commit()
        return True
    return False


# ============ User Management Services ============

def get_all_users_admin(db: Session) -> List[UserModel]:
    """Get all users with basic info (admin view)."""
    return db.query(UserModel).all()


def get_user_count(db: Session) -> int:
    """Get total user count."""
    return db.query(UserModel).count()


# ============ Dashboard Statistics Services ============

def get_dashboard_stats(db: Session) -> Dict[str, int]:
    """Get admin dashboard statistics."""
    total_users = db.query(UserModel).count()
    total_features = db.query(FeatureDefinition).count()
    total_predictions = db.query(PredictionRecord).count()
    
    return {
        "total_users": total_users,
        "total_features": total_features,
        "total_predictions": total_predictions
    }
