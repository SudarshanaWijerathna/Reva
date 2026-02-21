"""
API routes for dynamic feature management and predictions.
All routes require user authentication.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.auth.authentication import get_current_user
from backend.dynamic.repositories import (
    get_active_features,
    create_feature,
    create_prediction_record,
    get_user_predictions
)
from backend.dynamic.services import (
    validate_features,
    make_prediction
)
from backend.dynamic.schemas import (
    FeatureDefinition,
    PredictionRecord
)
from backend.dynamic.models import (
    FeatureCreate,
    FeatureOut,
    FeatureUpdate,
    PredictionRequest,
    PredictionResponse,
    PredictionRecordOut
)


# Type aliases
Database = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]


# ============ Features Router ============

features_router = APIRouter(
    prefix="/api/features",
    tags=["Features"],
    dependencies=[Depends(get_current_user)]
)


@features_router.get("/{model_type}", response_model=list[FeatureOut])
def get_features(
    model_type: str,
    db: Database,
    current_user: CurrentUser
):
    features = get_active_features(db, model_type)
    if not features:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No features found for model type: {model_type}"
        )
    return features




# ============ Predictions Router ============

predictions_router = APIRouter(
    prefix="/api/predictions",
    tags=["Predictions"],
    dependencies=[Depends(get_current_user)]
)


@predictions_router.post("/{model_type}", response_model=PredictionResponse)
def predict_value(
    model_type: str,
    request: PredictionRequest,
    db: Database,
    current_user: CurrentUser
):
    print(f"Received prediction request for model type: {model_type} with features: {request.features}")
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user token"
            )
        
        predicted_value = make_prediction(
            db=db,
            model_type=model_type,
            input_features=request.features,
            user_id=user_id
        )
        print(f"Predicted value: {predicted_value}, for model type: {model_type}")
        return PredictionResponse(
            predicted_value=predicted_value,
            model_type=model_type
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@predictions_router.get("/history", response_model=list[PredictionRecordOut])
def get_prediction_history(
    db: Database,
    current_user: CurrentUser,
    model_type: str = None
):
    # return list of prediction records for the user, optionally filtered by model type
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user token"
        )
    
    predictions = get_user_predictions(db, user_id, model_type)
    return predictions
