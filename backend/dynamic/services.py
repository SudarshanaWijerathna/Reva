
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.dynamic.repositories import (
    get_active_features,
    create_prediction_record
)
from backend.dynamic.schemas import FeatureDefinition, PredictionRecord
from backend.predictions.model_runtime import predict_with_active_model
from ml.rental_service.feature_schema import RENTAL_FEATURE_DEFINITIONS

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


LAND_REQUIRED_FEATURES = [
    (("land_size",), (int, float)),
    (("district",), str),
]

LAND_OPTIONAL_FEATURES = [
    (("location_text",), str),
    (("main_road",), bool),
    (("electricity",), bool),
    (("clear_deed",), bool),
    (("water",), bool),
    (("bank_loan",), bool),
    (("near_town",), bool),
    (("distance_to_town_m",), (int, float)),
    (("period",), str),
]


RENTAL_REQUIRED_FEATURES = [
    (("property_type",), str),
    (("location",), str),
]

RENTAL_OPTIONAL_FEATURES = [
    (("district",), str),
    (("furnishing_status",), str),
    (("source",), str),
    (("bedrooms",), (int, float)),
    (("bathrooms",), (int, float)),
    (("floor_area_sqft", "house_sqft", "house_sqft_capped", "size_sqft"), (int, float)),
    (("land_perches", "land_size_perches"), (int, float)),
    (("floor_number",), (int, float)),
    (("car_parking_spaces", "parking_spaces"), (int, float)),
    (("deposit_months",), (int, float)),
    (("advance_months",), (int, float)),
    (("lease_term_months",), (int, float)),
    (("posted_year",), (int, float)),
    (("posted_month",), (int, float)),
    (("is_short_term", "short_term"), bool),
    *((definition["name"],) for definition in RENTAL_FEATURE_DEFINITIONS if definition["data_type"] == "boolean"),
]


def get_builtin_features_for_model(model_type: str) -> list[dict[str, Any]]:
    if (model_type or "").strip().lower() != "rental":
        return []
    return [
        {
            "id": 100000 + index,
            "model_type": "rental",
            "active": True,
            **definition,
        }
        for index, definition in enumerate(RENTAL_FEATURE_DEFINITIONS, start=1)
    ]


def _validate_feature_contract(
    input_features: Dict[str, Any],
    required_features: list[tuple[tuple[str, ...], Any]],
    optional_features: list[tuple[tuple[str, ...], Any]] | None = None,
) -> None:
    errors = []
    for field_names, expected_type in required_features:
        field_name = next((name for name in field_names if name in input_features), field_names[0])
        if field_name not in input_features:
            errors.append(f"Required field '{field_names[0]}' is missing")
            continue
        value = input_features[field_name]
        if not _value_matches_type(value, expected_type):
            errors.append(f"Field '{field_name}' has an invalid value")

    for field_names, expected_type in optional_features or []:
        field_name = next((name for name in field_names if name in input_features), None)
        if not field_name:
            continue
        value = input_features[field_name]
        if value in {None, ""}:
            continue
        if not _value_matches_type(value, expected_type):
            errors.append(f"Field '{field_name}' has an invalid value")

    if errors:
        raise ValueError("; ".join(errors))


def _value_matches_type(value: Any, expected_type: Any) -> bool:
    if expected_type is bool:
        return isinstance(value, bool)
    if isinstance(expected_type, tuple):
        return isinstance(value, expected_type) and not isinstance(value, bool)
    return isinstance(value, expected_type) and not isinstance(value, bool)


def validate_builtin_house_features(input_features: Dict[str, Any]) -> None:
    _validate_feature_contract(input_features, HOUSE_REQUIRED_FEATURES)


def validate_builtin_land_features(input_features: Dict[str, Any]) -> None:
    _validate_feature_contract(input_features, LAND_REQUIRED_FEATURES, LAND_OPTIONAL_FEATURES)


def validate_builtin_rental_features(input_features: Dict[str, Any]) -> None:
    _validate_feature_contract(input_features, RENTAL_REQUIRED_FEATURES, RENTAL_OPTIONAL_FEATURES)


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
        elif model_type == "land":
            validate_builtin_land_features(input_features)
        elif model_type == "rental" and not feature_defs:
            validate_builtin_rental_features(input_features)
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



