"""
Runtime helpers for invoking the active registered model for predictions.
"""

import os
from typing import Any, Dict

from sqlalchemy.orm import Session

from backend.predictions.external_model_api import predict_via_http


MODEL_ENDPOINT_ENV_VARS = {
    "land": "LAND_MODEL_API_URL",
    "house": "HOUSE_MODEL_API_URL",
    "rental": "RENTAL_MODEL_API_URL",
}

EMBEDDED_RUNTIME_MODES = {"embedded", "inprocess", "in-process", "local"}


def _model_runtime_mode(model_type: str) -> str:
    specific_key = f"{model_type.upper()}_MODEL_RUNTIME"
    return os.getenv(specific_key, os.getenv("MODEL_RUNTIME_MODE", "service")).strip().lower()


def _predict_with_embedded_model(model_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if model_type == "land":
        from ml.land_service.service import predict_land_price

        return predict_land_price(payload)

    if model_type == "house":
        from ml.house_service.service import predict_house_price

        return predict_house_price(payload)

    if model_type == "rental":
        from ml.rental_service.service import predict_rental_price

        return predict_rental_price(payload)

    raise ValueError(f"No embedded model is available for model type: {model_type}")


def _env_endpoint_for(model_type: str) -> str:
    env_key = MODEL_ENDPOINT_ENV_VARS.get(model_type)
    if not env_key:
        return ""
    return os.getenv(env_key, "").strip()


def _is_embedded_endpoint(endpoint_url: str, model_type: str) -> bool:
    normalized = endpoint_url.strip().lower()
    return normalized in {
        "local",
        "local://",
        "local://embedded",
        f"local://{model_type}",
    }


def predict_with_active_model(
    db: Session,
    model_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Resolve the active model from the registry and execute a prediction against it.
    """
    from backend.admin.services import get_active_model_by_type

    model_type = (model_type or "").strip().lower()
    endpoint_url = _env_endpoint_for(model_type)

    if endpoint_url:
        if _is_embedded_endpoint(endpoint_url, model_type):
            return _predict_with_embedded_model(model_type, payload)
        return predict_via_http(model_type, endpoint_url, payload)

    active_model = get_active_model_by_type(db, model_type)
    endpoint_url = (active_model.deployed_endpoint or "").strip() if active_model else ""

    if endpoint_url:
        if _is_embedded_endpoint(endpoint_url, model_type):
            return _predict_with_embedded_model(model_type, payload)
        if not endpoint_url.startswith(("http://", "https://")):
            raise ValueError(
                f"Unsupported deployed endpoint format for '{model_type}': {endpoint_url}. "
                "Use an http(s) model service endpoint, or local://<model_type> for explicit embedded mode."
            )
        return predict_via_http(model_type, endpoint_url, payload)

    if _model_runtime_mode(model_type) in EMBEDDED_RUNTIME_MODES:
        return _predict_with_embedded_model(model_type, payload)

    env_key = MODEL_ENDPOINT_ENV_VARS.get(model_type, f"{model_type.upper()}_MODEL_API_URL")
    raise ValueError(
        f"No model service endpoint is configured for '{model_type}'. "
        f"Run the {model_type} ML service locally and set {env_key}, "
        "or register an active model endpoint in the admin model registry."
    )
