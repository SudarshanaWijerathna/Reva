from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd

from ml.land_service.feature_engineering import derive_features
from ml.land_service.time_calibration import adjust_price


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.joblib"

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
FEATURES = bundle["features"]
CAT_COLS = bundle["cat_cols"]
CAT_MAPS = bundle["cat_maps"]


def predict_land_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    features = derive_features(payload)
    frame = pd.DataFrame([features])[FEATURES]

    for column in CAT_COLS:
        frame[column] = pd.Categorical(frame[column], categories=CAT_MAPS[column])

    base_price = float(model.predict(frame)[0])
    adjusted_price = adjust_price(
        predicted_price=base_price,
        district=payload["district"],
        target_period=payload.get("period", "2025 H2"),
    )

    return {
        "predicted_value": round(adjusted_price, 2),
        "base_price_per_perch": round(base_price, 2),
        "adjusted_price_per_perch": round(adjusted_price, 2),
        "district": payload["district"],
        "period": payload.get("period", "2025 H2"),
        "model_type": "land",
    }
