from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ml.rental_service.service import is_model_ready, predict_rental_price


app = FastAPI(title="Reva Rental Model Service")


class PredictionRequest(BaseModel):
    features: Dict[str, Any]


@app.get("/health")
def health_check():
    return {
        "status": "ok" if is_model_ready() else "degraded",
        "model_type": "rental",
        "model_ready": is_model_ready(),
    }


@app.post("/predict")
def predict(request: PredictionRequest):
    try:
        return predict_rental_price(request.features)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
