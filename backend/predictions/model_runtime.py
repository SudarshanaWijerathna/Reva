"""
Runtime helpers for invoking the active registered model for predictions.
"""

from typing import Any, Dict

from sqlalchemy.orm import Session

from backend.admin.services import get_active_model_by_type
from backend.predictions.external_model_api import predict_via_http


def predict_with_active_model(
    db: Session,
    model_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Resolve the active model from the registry and execute a prediction against it.
    """
#
    active_model = get_active_model_by_type(db, model_type)
    if not active_model:
        raise ValueError(f"No active model found for model type: {model_type}")
    
    
    endpoint_url = (active_model.deployed_endpoint or "").strip()
    if not endpoint_url:
        raise ValueError(f"Active model for '{model_type}' has no deployed endpoint configured")

    if not endpoint_url.startswith(("http://", "https://")):
        raise ValueError(
            f"Unsupported deployed endpoint format for '{model_type}': {endpoint_url}. "
            "Active models must use an http(s) deployed endpoint."
        )

    return predict_via_http(model_type, endpoint_url, payload)
