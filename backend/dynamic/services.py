
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
from backend.predictions import market_index
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

# API model type -> market-index asset name.
MODEL_TYPE_TO_ASSET = {"house": "house", "land": "land", "rental": "rental"}

# Confidence in the *price*, which is the model's output moved by the index.
#
# A stale index does not make the price wrong - the anchor factor falls back to
# exactly 1.0, which is the naive forecast, and the backtest says naive is the
# best available method anyway. It does mean the price is quoted at the model's
# anchor rather than at today, so it costs one step of confidence rather than
# collapsing the answer. "degraded" is reserved for a failure of the model itself.
CONFIDENCE_ORDER = ["high", "medium", "low"]

# Default unit per model type, used when a model does not declare its own.
DEFAULT_UNITS = {"land": "LKR_per_perch", "house": "LKR_total", "rental": "LKR_per_month"}

# Fallback plausibility band for the forecast path, used only when a series
# ships no manifest bound. Per-series bounds derived from realised volatility
# are far tighter and are preferred; see max_plausible_monthly_move in each
# LSTM manifest.
MIN_GROWTH_FACTOR = 0.5
MAX_GROWTH_FACTOR = 2.5

# Beyond this the published index is too old to project across, so the forecast
# path is dropped rather than extended over the gap.
MAX_INDEX_STALENESS_MONTHS = int(os.getenv("MAX_INDEX_STALENESS_MONTHS", "12"))


def _step_down(level: str) -> str:
    position = CONFIDENCE_ORDER.index(level)
    return CONFIDENCE_ORDER[min(position + 1, len(CONFIDENCE_ORDER) - 1)]


def _combined_confidence(model_confidence: str | None, index_confidence: str | None) -> str:
    """
    Compose the model's coverage confidence with the index's.

    The model's coverage leads, because it determines whether the price is about
    this property at all. An index that could not supply a time adjustment costs
    one step; a proxy or approximated month costs nothing, since those shift the
    factor slightly rather than removing it.
    """
    level = model_confidence if model_confidence in CONFIDENCE_ORDER else "medium"
    if index_confidence == "degraded":
        level = _step_down(level)
    return level


def _lstm_index_enabled(model_type: str) -> bool:
    """
    Kill switch for the LSTM forecast path, per asset or globally.

    Set ``LSTM_INDEX_ENABLED=false`` to disable every forecast, or
    ``HOUSE_LSTM_INDEX_ENABLED=false`` for one asset. Disabling only flattens the
    forecast path; the per-property price from the ML model is unaffected.
    """
    specific = os.getenv(f"{model_type.upper()}_LSTM_INDEX_ENABLED")
    # Forecasts stay disabled until an LSTM beats the naive and drift baselines
    # for the horizon it claims to support. Current repository backtests do not.
    raw = specific if specific is not None else os.getenv("LSTM_INDEX_ENABLED", "false")
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
    Return unitless growth factors from the market index.

    Each factor is ``index[step] / index[latest_published]``, so the caller can
    rescale any absolute price onto the forecast trajectory. Anchoring on the last
    published value rather than on the first forecast is deliberate: it keeps the
    model's jump out of the last actual visible to the plausibility check below,
    instead of normalising it away.

    Returns an empty list - meaning "no trend information" - when the index is
    unavailable, stale, or implies a move the series has never made.
    """
    series_key = LSTM_SERIES_KEYS.get(model_type)
    if not series_key:
        return []

    if not _lstm_index_enabled(model_type):
        logger.info("Market index disabled for '%s' by configuration.", model_type)
        return []

    try:
        lstm_results = get_future_predictions() or {}
    except Exception as exc:
        logger.warning("Market index unavailable for '%s': %s", model_type, exc)
        return []

    series = lstm_results.get(series_key) or {}
    if series.get("error"):
        logger.warning("Market index for '%s' reported an error: %s", model_type, series["error"])
        return []

    staleness = series.get("staleness_months")
    if staleness is not None and int(staleness) > MAX_INDEX_STALENESS_MONTHS:
        logger.warning(
            "Market index for '%s' ends %s (%s months ago); refusing to extrapolate "
            "across the gap. Refresh it with scripts/build_market_index.py.",
            model_type,
            series.get("series_end"),
            staleness,
        )
        return []

    path: list[float] = []
    for item in (series.get("forecast_path") or series.get("next_5_close") or [])[:steps]:
        try:
            path.append(_to_number(item))
        except (TypeError, ValueError):
            continue
    if not path:
        return []

    # Anchor on the last published value; fall back to the first forecast only if
    # the snapshot predates this field.
    try:
        base = _to_number(series["latest_index"])
    except (KeyError, TypeError, ValueError):
        base = path[0]
    if base <= 0:
        return []

    factors = [value / base for value in path]

    # Per-step move the series has actually exhibited, from the manifest.
    limit = series.get("max_plausible_monthly_move")
    if limit:
        limit = float(limit)
        moves = [factors[0] - 1.0] + [
            factors[i] / factors[i - 1] - 1.0 for i in range(1, len(factors))
        ]
        if any(abs(move) > limit for move in moves):
            logger.warning(
                "Market index for '%s' implies monthly moves %s beyond the +/-%.4f band this "
                "series has exhibited; ignoring the forecast path.",
                model_type,
                [round(move, 4) for move in moves],
                limit,
            )
            return []

    if any(factor < MIN_GROWTH_FACTOR or factor > MAX_GROWTH_FACTOR for factor in factors):
        logger.warning(
            "Market index for '%s' produced implausible growth factors %s; "
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

        # 1. The per-property model owns the price level, at its own anchor period.
        results = predict_with_active_model(
            db=db,
            model_type=model_type,
            payload=input_features,
        )
        anchor_value = float(results["predicted_value"])

        # 2. The index moves that level from the model's anchor to today. A
        #    degraded factor is exactly 1.0, so an unusable index leaves the
        #    model's own number untouched rather than distorting it.
        asset = MODEL_TYPE_TO_ASSET[model_type]
        anchor_factor = market_index.growth_factor(
            asset,
            anchor_period=input_features.get("period") if model_type == "land" else None,
        )
        predicted_value = anchor_value * anchor_factor.value

        # 3. The forecast supplies the forward path, as a ratio against the last
        #    published index value.
        predicted_sequence, sequence_source = _forward_price_path(model_type, predicted_value)

        # Models that already return a ``details`` block (rental) have it merged in
        # rather than nested, so every consumer reads one flat namespace.
        details: Dict[str, Any] = dict(results)
        nested_details = details.pop("details", None)
        if isinstance(nested_details, dict):
            details.update(nested_details)

        details["anchor_adjustment"] = {
            "model_price_at_anchor": round(anchor_value, 2),
            "factor": round(anchor_factor.value, 6),
            "applied": bool(anchor_factor.is_usable and anchor_factor.value != 1.0),
            **anchor_factor.as_dict(),
        }
        details["sequence_source"] = sequence_source
        details["market_index"] = market_index.describe(asset)

        confidence = _combined_confidence(results.get("confidence"), anchor_factor.confidence)
        details["confidence_inputs"] = {
            "model_coverage": results.get("confidence"),
            "index": anchor_factor.confidence,
        }

        if user_id:
            prediction_record = PredictionRecord(
                user_id=user_id,
                model_type=model_type,
                features=input_features,
                predicted_value=str(predicted_value),
            )
            create_prediction_record(db, prediction_record)

        payload_out = {
            "predicted_value": predicted_value,
            "predicted_sequence": predicted_sequence,
            "model_type": model_type,
            "confidence": confidence,
            "unit": results.get("unit") or DEFAULT_UNITS.get(model_type),
            "details": details,
        }
        if results.get("total_value") is not None:
            # Land is quoted per perch; the whole-plot figure travels alongside it
            # and is moved by the same anchor factor.
            payload_out["total_value"] = round(
                float(results["total_value"]) * anchor_factor.value, 2
            )
        return payload_out

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

    user = {"id": user_id} if user_id else {}
    try:
        recommendations = get_reccomendations(user, db)
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
    
   


