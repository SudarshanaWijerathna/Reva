from flask import Blueprint, request, jsonify
import pandas as pd
import joblib

from backend.ml.land.feature_engineering import derive_features
from backend.ml.land.time_calibration import adjust_price

land_bp = Blueprint("land_bp", __name__)

# Load model once
MODEL_PATH = "backend/ml/land/model.joblib"
bundle = joblib.load(MODEL_PATH)

model = bundle["model"]
FEATURES = bundle["features"]
CAT_COLS = bundle["cat_cols"]
CAT_MAPS = bundle["cat_maps"]


@land_bp.route("/predict/land", methods=["POST"])
def predict_land_price():
    data = request.json

    # 1. Feature engineering
    features = derive_features(data)
    X = pd.DataFrame([features])[FEATURES]

    # 2. Re-apply categorical metadata (CRITICAL for LightGBM)
    for col in CAT_COLS:
        X[col] = pd.Categorical(X[col], categories=CAT_MAPS[col])

    # 3. Base prediction
    base_price = float(model.predict(X)[0])

    # 4. Optional time calibration
    period = data.get("period", "2025 H2")
    district = data["district"]

    adjusted_price = adjust_price(
        predicted_price=base_price,
        district=district,
        target_period=period
    )

    return jsonify({
        "base_price_per_perch": round(base_price, 2),
        "adjusted_price_per_perch": round(adjusted_price, 2),
        "district": district,
        "period": period
    })
