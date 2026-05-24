
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.dynamic.repositories import (
    get_active_features,
    create_prediction_record
)
from backend.dynamic.schemas import FeatureDefinition, PredictionRecord
from backend.predictions.model_runtime import predict_with_active_model

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


HOUSE_REQUIRED_FEATURES = [
    (("house_sqft", "house_sqft_capped"), (int, float)),
    (("land_sqft", "land_sqft_capped"), (int, float)),
    (("bedrooms",), int),
    (("bathrooms",), int),
    (("lat",), (int, float)),
    (("lon",), (int, float)),
    (("district",), str),
    (("sub_location",), str),
    (("posted_year",), int),
    (("posted_month",), int),
]


def validate_builtin_house_features(input_features: Dict[str, Any]) -> None:
    errors = []
    for field_names, expected_type in HOUSE_REQUIRED_FEATURES:
        field_name = next((name for name in field_names if name in input_features), field_names[0])
        if field_name not in input_features:
            errors.append(f"Required field '{field_names[0]}' is missing")
            continue
        value = input_features[field_name]
        if isinstance(expected_type, tuple):
            is_valid = isinstance(value, expected_type) and not isinstance(value, bool)
        else:
            is_valid = isinstance(value, expected_type) and not isinstance(value, bool)
        if not is_valid:
            errors.append(f"Field '{field_name}' has an invalid value")

    if errors:
        raise ValueError("; ".join(errors))


# ============ Prediction Services ============

def make_prediction(
    db: Session,
    model_type: str,
    input_features: Dict[str, Any],
    user_id: int
) -> Dict[str, Any]:
    """Make a prediction for the specified model type."""
    
    try:
        model_type = (model_type or "").strip().lower()

        # Get active features and validate
        feature_defs = get_active_features(db, model_type)
        if model_type == "house":
            validate_builtin_house_features(input_features)
        elif feature_defs:
            validate_features(feature_defs, input_features)
        else:
            raise ValueError(f"No feature definitions found for model type: {model_type}")

        if model_type not in {"land", "house", "rental"}:
            raise ValueError(f"Unknown model type: {model_type}")

        results = predict_with_active_model(
            db=db,
            model_type=model_type,
            payload=input_features,
        )
        predicted_value = float(results["predicted_value"])

        prediction_record = PredictionRecord(
            user_id=user_id,
            model_type=model_type,
            features=input_features,
            predicted_value=str(predicted_value),
        )
        create_prediction_record(db, prediction_record)
        return results
    
    except ValueError as e:
        raise ValueError(f"Prediction validation error: {str(e)}")
    except KeyError as e:
        raise KeyError(f"Missing required key in prediction results: {str(e)}")
    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")



