"""
Service layer for admin operations.
Handles business logic for admin features and user management.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.dynamic.schemas import FeatureDefinition, PredictionRecord
from backend.database.schemas import UserModel
from backend.admin.db_models import ModelRegistry


ALLOWED_MODEL_TYPES = {"land", "house", "rental"}


def _normalize_model_type(model_type: str) -> str:
    """Normalize and validate model type values used by admins."""
    normalized = (model_type or "").strip().lower()
    if normalized not in ALLOWED_MODEL_TYPES:
        raise ValueError(
            f"Invalid model_type '{model_type}'. Allowed: {', '.join(sorted(ALLOWED_MODEL_TYPES))}"
        )
    return normalized


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


# ============ Model Registry Services ============

def get_all_models_admin(
    db: Session,
    model_type: str = None,
    active_only: bool = False
) -> List[ModelRegistry]:
    """List all model registry records with optional filters."""
    query = db.query(ModelRegistry)

    if model_type:
        query = query.filter(ModelRegistry.model_type == _normalize_model_type(model_type))
    if active_only:
        query = query.filter(ModelRegistry.is_active.is_(True))

    return query.order_by(ModelRegistry.created_at.desc()).all()


def get_model_by_id_admin(db: Session, model_id: int) -> ModelRegistry:
    """Get one model registry record by ID."""
    return db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()


def _deactivate_models_for_type(db: Session, model_type: str) -> None:
    """Ensure only one model remains active per model type."""
    db.query(ModelRegistry).filter(
        ModelRegistry.model_type == model_type,
        ModelRegistry.is_active.is_(True)
    ).update({"is_active": False}, synchronize_session=False)


def create_model_admin(
    db: Session,
    model_data: Dict[str, Any],
    uploaded_by_email: str = None
) -> ModelRegistry:
    """Create a model registry record. Optionally set it active."""
    payload = dict(model_data)
    payload["model_type"] = _normalize_model_type(payload.get("model_type"))
    payload["uploaded_by_email"] = uploaded_by_email

    should_activate = bool(payload.get("is_active"))
    if should_activate:
        _deactivate_models_for_type(db, payload["model_type"])

    new_model = ModelRegistry(**payload)
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return new_model


def update_model_admin(
    db: Session,
    model_id: int,
    model_data: Dict[str, Any]
) -> ModelRegistry:
    """Update model registry metadata and activation state."""
    db_model = get_model_by_id_admin(db, model_id)
    if not db_model:
        return None

    payload = dict(model_data)
    if "model_type" in payload and payload["model_type"] is not None:
        payload["model_type"] = _normalize_model_type(payload["model_type"])

    target_model_type = payload.get("model_type", db_model.model_type)
    should_activate = payload.get("is_active") is True

    if should_activate:
        _deactivate_models_for_type(db, target_model_type)

    for key, value in payload.items():
        if value is not None:
            setattr(db_model, key, value)

    db.commit()
    db.refresh(db_model)
    return db_model


def activate_model_admin(db: Session, model_id: int) -> ModelRegistry:
    """Activate one model and deactivate other active models in that type."""
    db_model = get_model_by_id_admin(db, model_id)
    if not db_model:
        return None

    _deactivate_models_for_type(db, db_model.model_type)
    db_model.is_active = True
    db.commit()
    db.refresh(db_model)
    return db_model


def delete_model_admin(db: Session, model_id: int) -> bool:
    """Delete one model registry record."""
    db_model = get_model_by_id_admin(db, model_id)
    if not db_model:
        return False

    db.delete(db_model)
    db.commit()
    return True
