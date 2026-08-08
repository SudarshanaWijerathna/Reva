from pathlib import Path
from typing import Any, Dict
import json

import pandas as pd
from catboost import CatBoostRegressor, Pool

from ml.house_service.description_features import (
    DESCRIPTION_FEATURES,
    FEATURE_EXTRACTION_VERSION,
    extract_description_features,
)
from ml.house_service.feature_schema import BASELINE_CATEGORICAL_COLUMNS, BASELINE_FEATURES

try:
    from ml.house_service.gnn.schema import (
        IMPUTABLE_BINARY_COLUMNS,
        IMPUTABLE_CATEGORICAL_COLUMNS,
        IMPUTABLE_NUMERIC_COLUMNS,
    )
except ImportError:
    IMPUTABLE_NUMERIC_COLUMNS = [
        "land_sqft_capped",
        "bedrooms",
        "bathrooms",
        "road_width_ft",
        "parking_spaces",
        "distance_to_town_km",
        "distance_to_hospital_km",
        "distance_to_school_km",
        "distance_to_supermarket_km",
        "distance_to_bus_or_rail_km",
        "utility_score",
        "road_access_score",
        "service_access_score",
        "quality_score",
        "description_value_index",
    ]
    IMPUTABLE_BINARY_COLUMNS = [
        "mentions_main_road",
        "mentions_carpet_road",
        "mentions_private_lane",
        "water_available",
        "electricity_available",
        "solar_power_available",
        "hot_water_available",
        "brand_new",
        "fully_furnished",
        "air_conditioned",
        "cctv",
        "servant_room",
        "pantry",
        "garden",
        "mentions_school",
        "mentions_hospital",
        "mentions_supermarket",
        "mentions_bank",
        "mentions_highway",
        "mentions_junction",
    ]
    IMPUTABLE_CATEGORICAL_COLUMNS = ["house_quality_tier"]

try:
    from ml.house_service.gnn.inference import gnn_response_metadata, load_optional_gnn_predictor
except ImportError:
    def load_optional_gnn_predictor(_base_dir: Path) -> None:
        return None

    def gnn_response_metadata(_result: Any) -> Dict[str, Any]:
        return {}


BASE_DIR = Path(__file__).resolve().parent
BASELINE_MODEL_PATH = BASE_DIR / "catboost_house_price_baseline.cbm"
ENHANCED_MODEL_PATH = BASE_DIR / "catboost_house_price_enhanced.cbm"
METADATA_PATH = BASE_DIR / "catboost_house_price_enhanced_metadata.json"

HOUSE_SQFT_MIN = 800.0
LAND_SQFT_MIN = 1000.0

metadata: Dict[str, Any] = {}
model_variant = "baseline"
MODEL_PATH = BASELINE_MODEL_PATH
FEATURES = BASELINE_FEATURES
CATEGORICAL_COLUMNS = BASELINE_CATEGORICAL_COLUMNS

if ENHANCED_MODEL_PATH.exists() and METADATA_PATH.exists():
    with METADATA_PATH.open("r", encoding="utf-8") as file:
        metadata = json.load(file)
    MODEL_PATH = ENHANCED_MODEL_PATH
    FEATURES = metadata.get("features", BASELINE_FEATURES)
    CATEGORICAL_COLUMNS = metadata.get("categorical_columns", BASELINE_CATEGORICAL_COLUMNS)
    model_variant = metadata.get("model_variant", "enhanced")

model = CatBoostRegressor()
model.load_model(str(MODEL_PATH))
gnn_predictor = load_optional_gnn_predictor(BASE_DIR)


def _require_field(payload: Dict[str, Any], field_name: str) -> Any:
    value = payload.get(field_name)
    if value is None or value == "":
        raise ValueError(f"Missing required field: {field_name}")
    return value


def _field_is_missing(payload: Dict[str, Any], *field_names: str) -> bool:
    return all(payload.get(field_name) is None or payload.get(field_name) == "" for field_name in field_names)


def _optional_numeric_feature(
    payload: Dict[str, Any],
    canonical_name: str,
    fallback: float,
    missing_fields: set[str],
    allow_missing: bool,
    *payload_names: str,
) -> float:
    for payload_name in payload_names:
        value = payload.get(payload_name)
        if value is not None and value != "":
            return float(value)
    if allow_missing:
        missing_fields.add(canonical_name)
        return fallback
    raise ValueError(f"Missing required field: {canonical_name}")


def _normalize_feature_dict(payload: Dict[str, Any], allow_missing: bool = False) -> tuple[Dict[str, Any], set[str]]:
    house_sqft = float(payload.get("house_sqft_capped") or payload.get("house_sqft") or 0)

    if house_sqft <= 0:
        raise ValueError("house_sqft_capped or house_sqft must be provided and greater than 0")

    missing_fields: set[str] = set()
    land_sqft = _optional_numeric_feature(
        payload,
        "land_sqft_capped",
        LAND_SQFT_MIN,
        missing_fields,
        allow_missing,
        "land_sqft_capped",
        "land_sqft",
    )
    bedrooms = _optional_numeric_feature(payload, "bedrooms", 3.0, missing_fields, allow_missing, "bedrooms")
    bathrooms = _optional_numeric_feature(payload, "bathrooms", 2.0, missing_fields, allow_missing, "bathrooms")

    normalized = {
        "house_sqft_capped": max(house_sqft, HOUSE_SQFT_MIN),
        "land_sqft_capped": max(land_sqft, LAND_SQFT_MIN),
        "bedrooms": int(round(bedrooms)),
        "bathrooms": int(round(bathrooms)),
        "lat": float(_require_field(payload, "lat")),
        "lon": float(_require_field(payload, "lon")),
        "district": str(_require_field(payload, "district")).strip().lower(),
        "sub_location": str(payload.get("sub_location") or "unknown").strip().lower() or "unknown",
        "posted_year": int(_require_field(payload, "posted_year")),
        "posted_month": int(_require_field(payload, "posted_month")),
    }

    description = payload.get("description") or payload.get("description_raw") or payload.get("ad_description") or ""
    description_features = extract_description_features(description)
    normalized.update(description_features)

    if int(description_features.get("road_width_missing", 1)):
        missing_fields.add("road_width_ft")
    if int(description_features.get("parking_spaces_missing", 1)):
        missing_fields.add("parking_spaces")
    for column in [
        "distance_to_town_km",
        "distance_to_hospital_km",
        "distance_to_school_km",
        "distance_to_supermarket_km",
        "distance_to_bus_or_rail_km",
    ]:
        if int(description_features.get(f"{column}_missing", 1)):
            missing_fields.add(column)
    if not str(description).strip():
        missing_fields.update(IMPUTABLE_BINARY_COLUMNS)
        missing_fields.update(IMPUTABLE_CATEGORICAL_COLUMNS)

    for column in IMPUTABLE_NUMERIC_COLUMNS + IMPUTABLE_BINARY_COLUMNS + IMPUTABLE_CATEGORICAL_COLUMNS:
        normalized[f"{column}_is_missing"] = 1.0 if column in missing_fields else 0.0

    return normalized, missing_fields


def _frame_from_features(features: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([[features.get(column, 0) for column in FEATURES]], columns=FEATURES)


def _normalize_payload(payload: Dict[str, Any]) -> pd.DataFrame:
    normalized, _ = _normalize_feature_dict(payload, allow_missing=False)
    return _frame_from_features(normalized)


def _predict_price_per_sqft_from_features(features: Dict[str, Any]) -> float:
    frame = _frame_from_features(features)
    inference_pool = Pool(frame, cat_features=CATEGORICAL_COLUMNS)
    return float(model.predict(inference_pool)[0])


def predict_house_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized, missing_fields = _normalize_feature_dict(payload, allow_missing=gnn_predictor is not None)
    gnn_metadata: Dict[str, Any] = {}
    fallback_reason = ""

    if gnn_predictor is not None:
        try:
            gnn_result = gnn_predictor.predict(normalized, missing_fields, _predict_price_per_sqft_from_features)
            predicted_price_per_sqft = gnn_result.predicted_price_per_sqft
            gnn_metadata = gnn_response_metadata(gnn_result)
        except Exception as exc:
            fallback_reason = str(exc)
            if missing_fields.intersection({"land_sqft_capped", "bedrooms", "bathrooms"}):
                raise ValueError(f"GNN imputation failed and required fields are missing: {fallback_reason}") from exc
            predicted_price_per_sqft = _predict_price_per_sqft_from_features(normalized)
    else:
        predicted_price_per_sqft = _predict_price_per_sqft_from_features(normalized)

    total_price = predicted_price_per_sqft * float(normalized["house_sqft_capped"])
    description_value_index = None
    if "description_value_index" in normalized:
        description_value_index = float(normalized["description_value_index"])
    elif any(feature in FEATURES for feature in DESCRIPTION_FEATURES):
        description = payload.get("description") or payload.get("description_raw") or payload.get("ad_description") or ""
        description_value_index = float(
            extract_description_features(description).get("description_value_index", 0.0)
        )

    response = {
        "predicted_value": round(total_price, 2),
        "predicted_price_per_sqft": round(predicted_price_per_sqft, 2),
        "house_sqft_capped": float(normalized["house_sqft_capped"]),
        "model_type": "house",
        "model_variant": model_variant,
    }
    response.update(gnn_metadata)
    if fallback_reason:
        response["gnn_fallback_reason"] = fallback_reason

    if description_value_index is not None:
        response["description_value_index"] = round(description_value_index, 4)
        response["feature_extraction_version"] = metadata.get(
            "feature_extraction_version",
            FEATURE_EXTRACTION_VERSION,
        )

    return response
