from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.joblib"


def is_model_ready() -> bool:
    return MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 0


def _load_model():
    if not is_model_ready():
        raise RuntimeError(
            "Rental model artifact is missing or empty. "
            "Add a valid model.joblib before deploying the rental service."
        )
    return joblib.load(MODEL_PATH)


def predict_rental_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    model = _load_model()
    frame = pd.DataFrame([payload])
    predicted_value = float(model.predict(frame)[0])
    return {
        "predicted_value": round(predicted_value, 2),
        "model_type": "rental",
    }
