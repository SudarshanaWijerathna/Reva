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


def _require_field(payload: Dict[str, Any], field_name: str) -> Any:
    value = payload.get(field_name)
    if value is None or value == "":
        raise ValueError(f"Missing required field: {field_name}")
    return value


def _normalize_payload(payload: Dict[str, Any]) -> pd.DataFrame:
    house_sqft = float(payload.get("house_sqft_capped") or payload.get("house_sqft") or 0)
    land_sqft = float(payload.get("land_sqft_capped") or payload.get("land_sqft") or 0)

    if house_sqft <= 0:
        raise ValueError("house_sqft_capped or house_sqft must be provided and greater than 0")
    if land_sqft <= 0:
        raise ValueError("land_sqft_capped or land_sqft must be provided and greater than 0")

    normalized = {
        "house_sqft_capped": max(house_sqft, HOUSE_SQFT_MIN),
        "land_sqft_capped": max(land_sqft, LAND_SQFT_MIN),
        "bedrooms": int(_require_field(payload, "bedrooms")),
        "bathrooms": int(_require_field(payload, "bathrooms")),
        "lat": float(_require_field(payload, "lat")),
        "lon": float(_require_field(payload, "lon")),
        "district": str(_require_field(payload, "district")).strip().lower(),
        "sub_location": str(payload.get("sub_location") or "unknown").strip().lower() or "unknown",
        "posted_year": int(_require_field(payload, "posted_year")),
        "posted_month": int(_require_field(payload, "posted_month")),
    }

    description = payload.get("description") or payload.get("description_raw") or payload.get("ad_description") or ""
    normalized.update(extract_description_features(description))

    return pd.DataFrame([[normalized.get(column, 0) for column in FEATURES]], columns=FEATURES)


def predict_house_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    frame = _normalize_payload(payload)
    inference_pool = Pool(frame, cat_features=CATEGORICAL_COLUMNS)

    predicted_price_per_sqft = float(model.predict(inference_pool)[0])
    total_price = predicted_price_per_sqft * float(frame.iloc[0]["house_sqft_capped"])
    description_value_index = None
    if "description_value_index" in frame.columns:
        description_value_index = float(frame.iloc[0]["description_value_index"])
    elif any(feature in FEATURES for feature in DESCRIPTION_FEATURES):
        description = payload.get("description") or payload.get("description_raw") or payload.get("ad_description") or ""
        description_value_index = float(
            extract_description_features(description).get("description_value_index", 0.0)
        )

    response = {
        "predicted_value": round(total_price, 2),
        "predicted_price_per_sqft": round(predicted_price_per_sqft, 2),
        "house_sqft_capped": float(frame.iloc[0]["house_sqft_capped"]),
        "model_type": "house",
        "model_variant": model_variant,
    }

    if description_value_index is not None:
        response["description_value_index"] = round(description_value_index, 4)
        response["feature_extraction_version"] = metadata.get(
            "feature_extraction_version",
            FEATURE_EXTRACTION_VERSION,
        )

    return response
