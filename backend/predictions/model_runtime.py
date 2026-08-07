import os
from typing import Any, Dict
from sqlalchemy.orm import Session
from backend.admin.services import get_active_model_by_type
from backend.predictions.external_model_api import predict_via_http


def _predict_local(model_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute prediction using local ML model packages."""
    model_type = (model_type or "").strip().lower()

    if model_type == "land":
        from ml.land_service.service import predict_land_price
        return predict_land_price(payload)

    elif model_type == "house":
        from ml.house_service.service import predict_house_price
        house_sqft = payload.get("house_size_sqft") or payload.get("house_sqft") or payload.get("house_sqft_capped") or 1500
        land_size_perch = payload.get("land_size") or 15
        land_sqft = payload.get("land_sqft") or payload.get("land_sqft_capped") or (float(land_size_perch) * 160.0)

        house_payload = {
            "house_sqft": float(house_sqft),
            "land_sqft": float(land_sqft),
            "bedrooms": int(payload.get("bedrooms") or 3),
            "bathrooms": int(payload.get("bathrooms") or 2),
            "lat": float(payload.get("lat") or 6.9271),
            "lon": float(payload.get("lon") or 79.8612),
            "district": str(payload.get("district") or "colombo"),
            "sub_location": str(payload.get("location_text") or payload.get("sub_location") or "colombo"),
            "posted_year": int(payload.get("posted_year") or 2025),
            "posted_month": int(payload.get("posted_month") or 1),
        }
        return predict_house_price(house_payload)

    elif model_type == "rental":
        from ml.rental_service.service import is_model_ready, predict_rental_price
        if is_model_ready():
            return predict_rental_price(payload)
        
        # Fallback estimation heuristic for rental when artifact is missing
        bedrooms = int(payload.get("bedrooms") or 2)
        bathrooms = int(payload.get("bathrooms") or 1)
        house_sqft = float(payload.get("house_size_sqft") or payload.get("house_sqft") or 1000)
        district = str(payload.get("district") or "colombo").lower()

        base_rate = 120.0 if "colombo" in district else 80.0
        estimated_rent = (house_sqft * base_rate) + (bedrooms * 15000) + (bathrooms * 8000)
        return {
            "predicted_value": round(estimated_rent, 2),
            "model_type": "rental"
        }

    else:
        raise ValueError(f"Unknown model type for local prediction: {model_type}")


def predict_with_active_model(
    db: Session,
    model_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a prediction against active registered model, falling back to local ML models if HTTP endpoints fail.
    """
    model_type = (model_type or "").strip().lower()
    use_local_first = os.getenv("USE_LOCAL_MODELS", "true").strip().lower() in ("true", "1", "yes")

    if use_local_first:
        try:
            return _predict_local(model_type, payload)
        except Exception as local_err:
            print(f"Local prediction failed for '{model_type}': {local_err}. Trying remote endpoint...")

    # Attempt remote endpoint
    active_model = get_active_model_by_type(db, model_type)
    if active_model and active_model.deployed_endpoint:
        endpoint_url = active_model.deployed_endpoint.strip()
        if endpoint_url.startswith(("http://", "https://")):
            try:
                return predict_via_http(model_type, endpoint_url, payload)
            except Exception as remote_err:
                print(f"Remote prediction failed for '{model_type}': {remote_err}. Falling back to local model...")

    # Final fallback to local
    return _predict_local(model_type, payload)

