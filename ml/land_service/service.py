"""
Land price model service.

Two things this returns that it did not before.

**A total.** ``predicted_value`` stays the price per perch, because that is the
unit the market quotes and the model predicts. ``total_value`` is added alongside
as ``price_per_perch x land_size``, so a caller does not have to know to multiply
and cannot forget to.

**A coverage verdict.** The model's district vocabulary holds only Colombo,
Gampaha and Kalutara, while the LVI calibration table names nine districts plus a
catch-all. Those two facts define three honest tiers, reported rather than hidden:

    high    in the model vocabulary and in the LVI table
    medium  in the LVI table but outside the model vocabulary, so the district
            reaches the tree as an unseen category and only the calibration is
            district-specific
    low     in neither, so the catch-all LVI row is used

A district outside the published set previously raised and failed the request.
It now returns a low-confidence estimate that says exactly why.
"""

from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd

from ml.land_service.feature_engineering import derive_features
from ml.land_service.time_calibration import DEFAULT_LAND_TYPE, available_districts, calibrate

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.joblib"

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
FEATURES = bundle["features"]
CAT_COLS = bundle["cat_cols"]
CAT_MAPS = bundle["cat_maps"]

# Districts the model was actually trained on.
MODEL_DISTRICTS = {str(value).strip().lower() for value in CAT_MAPS.get("district", [])}

SQFT_PER_PERCH = 272.25


def _coverage(district: str, used_fallback_district: bool) -> Dict[str, Any]:
    requested = str(district or "").strip()
    in_model = requested.lower() in MODEL_DISTRICTS

    if in_model and not used_fallback_district:
        confidence, note = "high", "District is in the model vocabulary and the LVI table."
    elif not used_fallback_district:
        confidence = "medium"
        note = (
            f"'{requested}' is outside the model's trained districts "
            f"({', '.join(sorted(MODEL_DISTRICTS))}), so it reaches the model as an unseen "
            "category. Only the LVI time calibration is district-specific here."
        )
    else:
        confidence = "low"
        note = (
            f"'{requested}' is in neither the model vocabulary nor the LVI table, so the "
            "table's 'All Others*' row was used. Treat this as an indicative figure."
        )

    return {
        "confidence": confidence,
        "note": note,
        "district_in_model_vocabulary": in_model,
        "used_fallback_lvi_row": used_fallback_district,
        "model_districts": sorted(MODEL_DISTRICTS),
        "lvi_districts": available_districts(DEFAULT_LAND_TYPE),
    }


def predict_land_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    features = derive_features(payload)
    frame = pd.DataFrame([features])[FEATURES]

    for column in CAT_COLS:
        frame[column] = pd.Categorical(frame[column], categories=CAT_MAPS[column])

    base_price = float(model.predict(frame)[0])
    period = payload.get("period", "2025 H2")

    calibration = calibrate(
        predicted_price=base_price,
        district=payload["district"],
        target_period=period,
    )
    adjusted = float(calibration["adjusted_price"])

    land_size = float(payload.get("land_size") or 0.0)
    total_value = round(adjusted * land_size, 2) if land_size > 0 else None
    coverage = _coverage(payload["district"], calibration["used_fallback_district"])

    return {
        # Per perch - the unit the market quotes and the model predicts.
        "predicted_value": round(adjusted, 2),
        "unit": "LKR_per_perch",
        # Whole-plot value, so callers never have to remember the multiplication.
        "total_value": total_value,
        "land_size_perches": land_size or None,
        "land_size_sqft": round(land_size * SQFT_PER_PERCH, 2) if land_size > 0 else None,
        "base_price_per_perch": round(base_price, 2),
        "adjusted_price_per_perch": round(adjusted, 2),
        "district": calibration["requested_district"],
        "period": period,
        "model_type": "land",
        "confidence": coverage["confidence"],
        "details": {
            "coverage": coverage,
            "calibration": {
                "matched_district": calibration["matched_district"],
                "multiplier": round(calibration["multiplier"], 6),
                "reference_period": calibration["reference_period"],
                "target_period": calibration["target_period"],
                "land_type": calibration["land_type"],
            },
        },
    }
