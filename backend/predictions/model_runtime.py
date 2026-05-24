"""
Runtime helpers for invoking the active registered model for predictions.
"""

import os
from typing import Any, Dict

from sqlalchemy.orm import Session

from backend.predictions.external_model_api import predict_via_http


def _predict_with_local_model(model_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if model_type == "house":
        from ml.house_service.service import predict_house_price

        return predict_house_price(payload)

    raise ValueError(f"No local fallback model is available for model type: {model_type}")


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
    active_model = get_active_model_by_type(db, model_type)
    if not active_model:
        return _predict_with_local_model(model_type, payload)

    endpoint_url = (active_model.deployed_endpoint or "").strip()
    if not endpoint_url:
        return _predict_with_local_model(model_type, payload)

    if endpoint_url in {f"local://{model_type}", "local"}:
        return _predict_with_local_model(model_type, payload)

    if model_type == "house" and os.getenv("HOUSE_MODEL_RUNTIME", "local").strip().lower() != "remote":
        return _predict_with_local_model(model_type, payload)

    if not endpoint_url.startswith(("http://", "https://")):
        raise ValueError(
            f"Unsupported deployed endpoint format for '{model_type}': {endpoint_url}. "
            "Active models must use an http(s) deployed endpoint or local://house."
        )

    try:
        return predict_via_http(model_type, endpoint_url, payload)
    except RuntimeError as exc:
        if model_type == "house":
            local_result = _predict_with_local_model(model_type, payload)
            local_result["model_runtime_fallback_reason"] = str(exc)
            return local_result
        raise
