
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.dynamic.repositories import (
    get_active_features,
    create_prediction_record
)
from backend.dynamic.schemas import FeatureDefinition, PredictionRecord
from backend.predictions.model_runtime import predict_with_active_model
from backend.core.cache_service import get_future_predictions, get_reccomendations

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
    user_id: int | None = None
) -> tuple[float, list[float]]:
    """Make a prediction for the specified model type."""
    
    try:
        model_type = (model_type or "").strip().lower()

        # Get active features and validate
        feature_defs = get_active_features(db, model_type)
        if not feature_defs:
            raise ValueError(f"No feature definitions found for model type: {model_type}")
        
        validate_features(feature_defs, input_features)

        if model_type not in {"land", "house", "rental"}:
            raise ValueError(f"Unknown model type: {model_type}")
        
        lstm_results = get_future_predictions() or {}
        property_key = "housing" if model_type == "house" else model_type
        property_predictions = lstm_results.get(property_key) or {}

        predicted_value = property_predictions.get("next_close")
        predicted_sequence = property_predictions.get("next_5_close") or []

        if predicted_value is None:
            raise ValueError(f"No future prediction available for model type: {model_type}")
        def normalize_number(value: Any) -> float:
            if isinstance(value, bool):
                raise ValueError("Invalid numeric value")
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                return float(value.replace(",", ""))
            raise ValueError("Invalid numeric value")

        if isinstance(predicted_value, str) or isinstance(predicted_value, (int, float)):
            predicted_value = normalize_number(predicted_value)

        if not predicted_sequence:
            predicted_sequence = [predicted_value * (1 + (idx + 1) * 0.015) for idx in range(5)]
        else:
            cleaned_sequence: list[float] = []
            for item in predicted_sequence:
                if item is None:
                    continue
                try:
                    cleaned_sequence.append(normalize_number(item))
                except ValueError:
                    continue
            predicted_sequence = cleaned_sequence


        '''results = predict_with_active_model(
            db=db,
            model_type=model_type,
            payload=input_features,
        )
        predicted_value = float(results["predicted_value"])'''

        if user_id:
            prediction_record = PredictionRecord(
                user_id=user_id,
                model_type=model_type,
                features=input_features,
                predicted_value=str(predicted_value),
            )
            create_prediction_record(db, prediction_record)
        return predicted_value, predicted_sequence

    except ValueError as e:
        raise ValueError(f"Prediction validation error: {str(e)}")
    except KeyError as e:
        raise KeyError(f"Missing required key in prediction results: {str(e)}")
    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")
    
def get_property_recommendation(
    db: Session,
    user_id: int,
    model_type: str
):
    normalized_type = (model_type or "").strip().lower()
    type_aliases = {"house": "housing"}
    normalized_type = type_aliases.get(normalized_type, normalized_type)

    property_order = ["land", "rental", "housing"]
    if normalized_type not in property_order:
        raise ValueError(f"Unknown model type: {model_type}")

    try:
        recommendations = get_reccomendations()
    except Exception:
        return {
            "model_type": normalized_type,
            "recommendation": "unavailable",
        }

    if not recommendations:
        return {
            "model_type": normalized_type,
            "recommendation": "unavailable",
        }

    action_labels = recommendations.get("action_labels")
    if not isinstance(action_labels, list) or len(action_labels) < len(property_order):
        return {
            "model_type": normalized_type,
            "recommendation": "unavailable",
        }

    label = action_labels[property_order.index(normalized_type)]
    return {
        "model_type": normalized_type,
        "recommendation": label,
        "action_index": recommendations.get("action_index"),
    }
    
   



