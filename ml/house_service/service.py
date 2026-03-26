from pathlib import Path
from typing import Any, Dict

import pandas as pd
from catboost import CatBoostRegressor, Pool


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "catboost_house_price_baseline.cbm"

FEATURES = [
    "house_sqft_capped",
    "land_sqft_capped",
    "bedrooms",
    "bathrooms",
    "lat",
    "lon",
    "district",
    "sub_location",
    "posted_year",
    "posted_month",
]

CATEGORICAL_COLUMNS = ["district", "sub_location"]

HOUSE_SQFT_MIN = 800.0
LAND_SQFT_MIN = 1000.0

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

    return pd.DataFrame([[normalized[column] for column in FEATURES]], columns=FEATURES)


def predict_house_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    frame = _normalize_payload(payload)
    inference_pool = Pool(frame, cat_features=CATEGORICAL_COLUMNS)

    predicted_price_per_sqft = float(model.predict(inference_pool)[0])
    total_price = predicted_price_per_sqft * float(frame.iloc[0]["house_sqft_capped"])

    return {
        "predicted_value": round(total_price, 2),
        "predicted_price_per_sqft": round(predicted_price_per_sqft, 2),
        "house_sqft_capped": float(frame.iloc[0]["house_sqft_capped"]),
        "model_type": "house",
    }
