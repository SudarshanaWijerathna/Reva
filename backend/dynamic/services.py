
import csv
import logging
import os
from collections import Counter
from functools import lru_cache
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Dict, Any
from backend.dynamic.repositories import (
    get_active_features,
    create_prediction_record
)
from backend.dynamic.schemas import FeatureDefinition, PredictionRecord
from backend.predictions.model_runtime import predict_with_active_model
from backend.core.cache_service import get_future_predictions, get_reccomendations
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
    *(
        ((definition["name"],), bool)
        for definition in RENTAL_FEATURE_DEFINITIONS
        if definition["data_type"] == "boolean"
    ),
]


@lru_cache(maxsize=1)
def _rental_dropdown_options() -> dict[str, list[str]]:
    options: dict[str, list[str]] = {
        "property_type": ["Apartment", "House", "Office space", "Annex", "Room", "Building", "Shop space", "Warehouse", "Villa"],
        "district": ["Colombo", "Gampaha", "Kalutara", "unknown"],
        "location": ["Colombo 5", "Colombo 3", "Colombo 2", "Dehiwala", "Nugegoda", "Rajagiriya", "Battaramulla"],
        "furnishing_status": ["furnished", "semi-furnished", "unfurnished", "unknown"],
    }
    feature_path = Path(__file__).resolve().parents[2] / "data" / "features" / "rental_features_v1.csv"
    if not feature_path.exists():
        return options

    counters = {column: Counter() for column in options}
    with feature_path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            for column, counter in counters.items():
                value = str(row.get(column) or "").strip()
                if value:
                    counter[value] += 1

    for column, counter in counters.items():
        if counter:
            values = [value for value, _ in counter.most_common()]
            if column == "furnishing_status":
                preferred = ["furnished", "semi-furnished", "unfurnished", "unknown"]
                values = preferred + [value for value in values if value not in preferred]
            options[column] = values
    return options


def get_builtin_features_for_model(model_type: str) -> list[dict[str, Any]]:
    if (model_type or "").strip().lower() != "rental":
        return []
    dropdown_options = _rental_dropdown_options()
    return [
        {
            "id": 100000 + index,
            "model_type": "rental",
            "active": True,
            "options": dropdown_options.get(definition["name"]),
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

logger = logging.getLogger(__name__)

# The LSTM series are market-level indices. Their absolute scale does not match
# the per-property models, so they are only ever consumed as ratios within a
# single series - never as prices.
LSTM_SERIES_KEYS = {"house": "housing", "land": "land", "rental": "rental"}

# A forecast that implies less than half or more than 2.5x the current value is
# treated as a broken series rather than a signal.
MIN_GROWTH_FACTOR = 0.5
MAX_GROWTH_FACTOR = 2.5


def _lstm_index_enabled(model_type: str) -> bool:
    """
    Kill switch for the LSTM forecast path, per asset or globally.

    Set ``LSTM_INDEX_ENABLED=false`` to disable every forecast, or
    ``HOUSE_LSTM_INDEX_ENABLED=false`` for one asset. Disabling only flattens the
    forecast path; the per-property price from the ML model is unaffected.
    """
    specific = os.getenv(f"{model_type.upper()}_LSTM_INDEX_ENABLED")
    raw = specific if specific is not None else os.getenv("LSTM_INDEX_ENABLED", "true")
    return raw.strip().lower() in ("true", "1", "yes", "on")


def _to_number(value: Any) -> float:
    """Coerce cache values such as '1,987,695.38' to float."""
    if isinstance(value, bool):
        raise ValueError("Invalid numeric value")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.replace(",", "").strip())
    raise ValueError("Invalid numeric value")


def _lstm_growth_factors(model_type: str, steps: int = 5) -> list[float]:
    """
    Return unitless step-over-step growth factors from the LSTM index.

    Each factor is ``index[step] / index[now]``, so the caller can rescale any
    absolute price onto the forecast trajectory. Returns an empty list when the
    index is unavailable or outside the plausible range.
    """
    series_key = LSTM_SERIES_KEYS.get(model_type)
    if not series_key:
        return []

    if not _lstm_index_enabled(model_type):
        logger.info("LSTM index disabled for '%s' by configuration.", model_type)
        return []

    try:
        lstm_results = get_future_predictions() or {}
    except Exception as exc:
        logger.warning("LSTM index unavailable for '%s': %s", model_type, exc)
        return []

    series = lstm_results.get(series_key) or {}
    raw_path = series.get("next_5_close") or []
    raw_base = series.get("next_close")

    path: list[float] = []
    for item in raw_path[:steps]:
        try:
            path.append(_to_number(item))
        except (TypeError, ValueError):
            continue

    if not path:
        return []

    try:
        base = _to_number(raw_base) if raw_base is not None else path[0]
    except (TypeError, ValueError):
        base = path[0]

    if base <= 0:
        return []

    factors = [value / base for value in path]
    if any(factor < MIN_GROWTH_FACTOR or factor > MAX_GROWTH_FACTOR for factor in factors):
        logger.warning(
            "LSTM index for '%s' produced implausible growth factors %s; "
            "ignoring the forecast path.",
            model_type,
            [round(factor, 4) for factor in factors],
        )
        return []
    return factors


def _forward_price_path(model_type: str, predicted_value: float, steps: int = 5) -> tuple[list[float], str]:
    """
    Project ``predicted_value`` forward using the LSTM index.

    Falls back to a flat path when no usable index exists - a flat path states
    'no trend information' honestly, instead of inventing a growth rate.
    """
    factors = _lstm_growth_factors(model_type, steps=steps)
    if not factors:
        return [round(predicted_value, 2)] * steps, "flat_no_index"

    path = [round(predicted_value * factor, 2) for factor in factors]
    while len(path) < steps:
        path.append(path[-1])
    return path, "lstm_index_ratio"


def make_prediction(
    db: Session,
    model_type: str,
    input_features: Dict[str, Any],
    user_id: int | None = None,
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

        # The per-property model owns the price level.
        results = predict_with_active_model(
            db=db,
            model_type=model_type,
            payload=input_features,
        )
        predicted_value = float(results["predicted_value"])

        # The LSTM index owns the forward trajectory, applied as a ratio.
        predicted_sequence, sequence_source = _forward_price_path(model_type, predicted_value)

        details: Dict[str, Any] = dict(results)
        details["sequence_source"] = sequence_source

        if user_id:
            prediction_record = PredictionRecord(
                user_id=user_id,
                model_type=model_type,
                features=input_features,
                predicted_value=str(predicted_value),
            )
            create_prediction_record(db, prediction_record)

        return {
            "predicted_value": predicted_value,
            "predicted_sequence": predicted_sequence,
            "model_type": model_type,
            "details": details,
        }

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
    
   



