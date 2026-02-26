from sqlalchemy.orm import Session
from backend.dynamic.schemas import FeatureDefinition, PredictionRecord


# ============ Feature Repositories ============

def get_active_features(db: Session, model_type: str):
    """Get all active feature definitions for a specific model type."""
    return db.query(FeatureDefinition)\
        .filter(
            FeatureDefinition.model_type == model_type,
            FeatureDefinition.active == True
        ).all()


def create_feature(db: Session, feature: FeatureDefinition):
    """Create a new feature definition."""
    db.add(feature)
    db.commit()
    db.refresh(feature)
    return feature


def get_feature_by_id(db: Session, feature_id: int):
    """Get a feature definition by ID."""
    return db.query(FeatureDefinition).filter(FeatureDefinition.id == feature_id).first()


def update_feature(db: Session, feature_id: int, feature_data: dict):
    """Update a feature definition."""
    db_feature = db.query(FeatureDefinition).filter(FeatureDefinition.id == feature_id).first()
    if db_feature:
        for key, value in feature_data.items():
            setattr(db_feature, key, value)
        db.commit()
        db.refresh(db_feature)
    return db_feature


# ============ Prediction Record Repositories ============

def create_prediction_record(db: Session, record: PredictionRecord):
    """Create a new prediction record."""
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user_predictions(db: Session, user_id: int, model_type: str = None):
    """Get prediction records for a specific user."""
    query = db.query(PredictionRecord).filter(PredictionRecord.user_id == user_id)
    if model_type:
        query = query.filter(PredictionRecord.model_type == model_type)
    return query.all()
