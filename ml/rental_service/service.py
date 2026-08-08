import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple

from ml.rental_service.feature_schema import (
    AMENITY_COLUMNS,
    CATEGORICAL_COLUMNS,
    DEFAULT_CATEGORICAL_VALUES,
    MODEL_VARIANT,
    NUMERIC_COLUMNS,
    REQUIRED_PREDICTION_COLUMNS,
    TRAINING_FEATURE_COLUMNS,
)


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "catboost_rental_price.cbm"
METADATA_PATH = BASE_DIR / "catboost_rental_price_metadata.json"


def is_model_ready() -> bool:
    return MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0 and METADATA_PATH.exists()


def _require_model_artifact() -> None:
    if not is_model_ready():
        raise RuntimeError(
            "Rental CatBoost model artifact is missing. "
            "Run ml/rental_service/train_model.py to create catboost_rental_price.cbm "
            "and catboost_rental_price_metadata.json."
        )


@lru_cache(maxsize=1)
def _load_model_bundle() -> Tuple[Any, Dict[str, Any]]:
    _require_model_artifact()
    try:
        from catboost import CatBoostRegressor
    except ImportError as exc:
        raise RuntimeError("catboost is required to serve the rental model.") from exc

    model = CatBoostRegressor()
    model.load_model(str(MODEL_PATH))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return model, metadata


def _clean_string(value: Any, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return text


def _coerce_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return float(int(value))
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def _coerce_binary(value: Any) -> int:
    if isinstance(value, str):
        return 1 if value.strip().lower() in {"1", "true", "yes", "y", "on"} else 0
    return 1 if bool(value) else 0


def _payload_alias(payload: Dict[str, Any], *names: str) -> Any:
    for name in names:
        value = payload.get(name)
        if value is None:
            continue
        if isinstance(value, str) and value == "":
            continue
        return value
    return None


def _normalize_feature_dict(payload: Dict[str, Any], metadata: Dict[str, Any] | None = None) -> Tuple[Dict[str, Any], set[str]]:
    features = list((metadata or {}).get("features") or TRAINING_FEATURE_COLUMNS)
    missing_fields: set[str] = set()
    normalized: Dict[str, Any] = {}

    for required in REQUIRED_PREDICTION_COLUMNS:
        if _payload_alias(payload, required) is None:
            missing_fields.add(required)

    aliases = {
        "floor_area_sqft": ("floor_area_sqft", "house_sqft", "house_sqft_capped", "size_sqft"),
        "land_perches": ("land_perches", "land_size_perches"),
        "car_parking_spaces": ("car_parking_spaces", "parking_spaces"),
        "is_short_term": ("is_short_term", "short_term"),
    }

    for feature in features:
        value = _payload_alias(payload, *(aliases.get(feature) or (feature,)))
        if feature in CATEGORICAL_COLUMNS:
            default = DEFAULT_CATEGORICAL_VALUES.get(feature, "unknown")
            normalized[feature] = _clean_string(value, default)
        elif feature in AMENITY_COLUMNS or feature in {"is_short_term", "has_description"}:
            normalized[feature] = _coerce_binary(value)
        elif feature == "description_length":
            description = _payload_alias(payload, "description", "description_raw", "ad_description")
            normalized[feature] = len(_clean_string(description, ""))
        elif feature in NUMERIC_COLUMNS or feature == "feature_anomaly_count":
            normalized[feature] = _coerce_float(value)
        else:
            normalized[feature] = _coerce_float(value)

    if _clean_string(_payload_alias(payload, "description", "description_raw", "ad_description"), ""):
        normalized["has_description"] = 1
    if normalized.get("furnishing_status") == "furnished":
        normalized["amenity_fully_furnished"] = 1
    normalized["amenity_count"] = sum(int(normalized.get(column, 0)) for column in AMENITY_COLUMNS)
    return normalized, missing_fields


def _frame_from_features(features: Dict[str, Any], feature_order: list[str]) -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas is required to serve the rental model.") from exc
    return pd.DataFrame([[features.get(column, 0) for column in feature_order]], columns=feature_order)


# Districts the rental corpus actually covers with volume.
COVERED_DISTRICTS = {"colombo", "gampaha", "kalutara"}


def _confidence(
    predicted_value: float,
    missing_fields: set[str],
    interval: Dict[str, float],
    payload: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Grade a rental estimate against what the model can actually support.

    This model generalises across properties far better than across time: its own
    training report holds out ``posted_year == 2026`` and records 58.8% MAPE with
    R2 0.25 on that period, against 32.0% MAPE and R2 0.71 in validation. The
    caveat is attached to every response rather than left in a JSON file, because
    a rent quoted without it reads more precise than it is.
    """
    notes: list[str] = []
    level = "high"

    if missing_fields:
        level = "low"
        notes.append(
            f"Required fields were absent and defaulted: {', '.join(sorted(missing_fields))}."
        )

    district = _clean_string(_payload_alias(payload, "district"), "").lower()
    if district and district not in COVERED_DISTRICTS:
        level = "low" if level == "low" else "medium"
        notes.append(
            f"'{district}' is outside the districts the rental corpus covers with volume "
            f"({', '.join(sorted(COVERED_DISTRICTS))}); treat this as indicative."
        )
    elif not district:
        level = "low" if level == "low" else "medium"
        notes.append("No district was supplied, so the estimate is not location-specific.")

    half_width = None
    if predicted_value > 0:
        half_width = (float(interval["upper"]) - float(interval["lower"])) / 2.0 / predicted_value
        # A p80 band wider than +/-50% of the estimate is too loose to call high.
        if half_width > 0.75:
            level = "low"
        elif half_width > 0.5 and level == "high":
            level = "medium"

    calibration = metadata.get("error_calibration") or {}
    temporal = ((metadata.get("metrics") or {}).get("temporal_test")) or {}

    return {
        "confidence": level,
        "notes": notes,
        "interval_half_width_pct": round(100 * half_width, 2) if half_width is not None else None,
        "relative_error_p80_pct": round(100 * float(calibration.get("relative_error_p80", 0.0)), 2),
        "temporal_caveat": (
            "Trained on pre-2026 listings and held out on 2026: "
            f"{temporal.get('mape', 58.8):.1f}% MAPE out of period versus "
            f"{((metadata.get('metrics') or {}).get('validation') or {}).get('mape', 32.0):.1f}% in "
            "validation. Rent levels drift faster than this model tracks them."
        ),
    }


def _prediction_interval(predicted_value: float, metadata: Dict[str, Any]) -> Dict[str, float]:
    """
    Multiplicative prediction interval around a rent estimate.

    The model is trained on log rent and inverted with ``expm1``, so its error is
    proportional rather than additive and the interval must be too.

    The previous additive form, ``max(value x relative_p80, absolute_p80)``, made
    the fixed 88,220 LKR absolute term dominate every low rent: a 74,368 estimate
    came back as [0, 162,588], implying a plausible rent of zero and rating a
    fully-specified Colombo house as *less* certain than a vague one. Dividing and
    multiplying by the same factor keeps the band symmetric in log space, strictly
    positive, and proportional at every price point.
    """
    calibration = metadata.get("error_calibration") or {}
    relative_error = float(calibration.get("relative_error_p80") or 0.15)
    factor = 1.0 + max(relative_error, 0.0)

    if predicted_value <= 0:
        return {"lower": 0.0, "upper": 0.0, "method": "multiplicative_p80", "factor": round(factor, 4)}

    return {
        "lower": round(predicted_value / factor, 2),
        "upper": round(predicted_value * factor, 2),
        "method": "multiplicative_p80",
        "factor": round(factor, 4),
    }


def predict_rental_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    model, metadata = _load_model_bundle()
    feature_order = list(metadata.get("features") or TRAINING_FEATURE_COLUMNS)
    categorical_columns = list(metadata.get("categorical_columns") or CATEGORICAL_COLUMNS)
    normalized, missing_fields = _normalize_feature_dict(payload, metadata)
    frame = _frame_from_features(normalized, feature_order)

    from catboost import Pool

    predicted_log_value = float(model.predict(Pool(frame, cat_features=categorical_columns))[0])
    predicted_value = max(math.expm1(predicted_log_value), 0.0)
    interval = _prediction_interval(predicted_value, metadata)
    grading = _confidence(predicted_value, missing_fields, interval, payload, metadata)

    return {
        "predicted_value": round(predicted_value, 2),
        "unit": "LKR_per_month",
        "model_type": "rental",
        "model_variant": metadata.get("model_variant", MODEL_VARIANT),
        "confidence": grading["confidence"],
        "details": {
            "schema_version": metadata.get("schema_version"),
            "target_inverse_transform": metadata.get("target_inverse_transform", "expm1"),
            "feature_count": len(feature_order),
            "missing_required_fields": sorted(missing_fields),
            "prediction_interval_lkr": interval,
            "coverage": {
                "confidence": grading["confidence"],
                "notes": grading["notes"],
                "covered_districts": sorted(COVERED_DISTRICTS),
            },
            "uncertainty": {
                "interval_half_width_pct": grading["interval_half_width_pct"],
                "relative_error_p80_pct": grading["relative_error_p80_pct"],
                "temporal_caveat": grading["temporal_caveat"],
            },
        },
    }
