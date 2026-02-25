
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.dynamic.repositories import (
    get_active_features,
    create_prediction_record
)
from backend.dynamic.schemas import FeatureDefinition, PredictionRecord
from backend.predictions.land_api import predict_land_price

# ============ Feature Validation Services ============

def validate_feature_type(value: Any, data_type: str) -> bool:

    #    Validate if a value matches the expected data type.
    
    if data_type == "boolean":
        return isinstance(value, bool)
    elif data_type == "float":
        return isinstance(value, (int, float))
    elif data_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    elif data_type == "string":
        return isinstance(value, str)
    return False


def validate_features(feature_defs: list[FeatureDefinition], input_features: Dict[str, Any]) -> list[str]:
  
    #   Validate input features against feature definitions.
    
    errors = []
    
    # Check for required fields
    for feature in feature_defs:
        if feature.required and feature.name not in input_features:
            errors.append(f"Required field '{feature.name}' is missing")
    
    if errors:
        raise ValueError("; ".join(errors))
    
    # Validate data types for provided fields
    for feature in feature_defs:
        if feature.name in input_features:
            value = input_features[feature.name]
            
            if not validate_feature_type(value, feature.data_type):
                raise ValueError(
                    f"Field '{feature.name}' must be of type '{feature.data_type}', "
                    f"got '{type(value).__name__}'"
                )
    
    return errors


# ============ Prediction Services ============

def make_prediction(
    db: Session,
    model_type: str,
    input_features: Dict[str, Any],
    user_id: int
) -> float:
    """Make a prediction for the specified model type."""
    
    try:
        # Get active features and validate
        feature_defs = get_active_features(db, model_type)
        if not feature_defs:
            raise ValueError(f"No feature definitions found for model type: {model_type}")
        
        validate_features(feature_defs, input_features)

        if model_type == "land":
            results = predict_land_price(input_features)
            predicted_value = results["adjusted_price_per_perch"]
            return predicted_value
        
        elif model_type == "house":
            # Placeholder for house price prediction logic
            return 0.0
        
        elif model_type == "rental":
            # Placeholder for rental price prediction logic
            return 0.0

        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    except ValueError as e:
        raise ValueError(f"Prediction validation error: {str(e)}")
    except KeyError as e:
        raise KeyError(f"Missing required key in prediction results: {str(e)}")
    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")



