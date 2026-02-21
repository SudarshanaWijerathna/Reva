from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
import joblib
from pathlib import Path

from backend.ml.land.feature_engineering import derive_features
from backend.ml.land.time_calibration import adjust_price

# ✅ FastAPI router (NOT Flask Blueprint)
land_bp = APIRouter(prefix="/predict", tags=["Land Prediction"])

# ---------------------------
# Load model once (startup)
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "land" / "model.joblib"

bundle = joblib.load(MODEL_PATH)

model = bundle["model"]
FEATURES = bundle["features"]
CAT_COLS = bundle["cat_cols"]
CAT_MAPS = bundle["cat_maps"]


'''
# ---------------------------
# Request Schema
# ---------------------------
class LandRequest(BaseModel):
    land_size: float
    district: str
    location_text: str | None = None
    main_road: bool = False
    electricity: bool = False
    clear_deed: bool = False
    water: bool = False
    bank_loan: bool = False
    near_town: bool = False
    distance_to_town_m: float = 0
    period: str = "2025 H2"

'''

#================= Kavishka ===============


def predict_land_price(payload: dict):

    print(f"Received payload: {payload}")
    # 1. Feature engineering
    features = derive_features(payload)
    X = pd.DataFrame([features])[FEATURES]

    # 2. Re-apply categorical metadata (CRITICAL for LightGBM)
    for col in CAT_COLS:
        X[col] = pd.Categorical(X[col], categories=CAT_MAPS[col])

    # 3. Base prediction
    base_price = float(model.predict(X)[0])

    # 4. Optional time calibration
    adjusted_price = adjust_price(
        predicted_price=base_price,
        district=payload["district"],
        target_period=payload.get("period", "2025 H2")
    )

    # ✅ FastAPI returns dict automatically (no jsonify)
    return {
        "base_price_per_perch": round(base_price, 2),
        "adjusted_price_per_perch": round(adjusted_price, 2),
        "district": payload["district"],
        "period": payload.get("period", "2025 H2")
    }