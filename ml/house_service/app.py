from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ml.house_service.service import predict_house_price


app = FastAPI(title="Reva House Model Service")


class PredictionRequest(BaseModel):
    features: Dict[str, Any]


@app.get("/health")
def health_check():
    return {"status": "ok", "model_type": "house"}


@app.post("/predict")
def predict(request: PredictionRequest):
    try:
        return predict_house_price(request.features)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
