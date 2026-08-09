"""
Runtime helpers for invoking the active registered model for predictions.

Resolution order for a given model type:

1. An explicit endpoint from the environment (``<TYPE>_MODEL_API_URL``).
   The sentinel values ``local`` / ``local://`` / ``local://<type>`` select the
   in-process ("embedded") model instead of an HTTP call.
2. An active endpoint registered in the admin model registry.
3. The runtime mode (``<TYPE>_MODEL_RUNTIME`` or ``MODEL_RUNTIME_MODE``), which
   defaults to embedded so a local checkout works without any configuration.

Remote calls degrade to the embedded model rather than failing the request,
because every model in ``ml/`` ships with its artifact in the repository.
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

# Embedded is the default so a fresh clone works with no environment set up.
# Set MODEL_RUNTIME_MODE=service to require an explicit endpoint instead.
DEFAULT_RUNTIME_MODE = "embedded"


def _model_runtime_mode(model_type: str) -> str:
    specific_key = f"{model_type.upper()}_MODEL_RUNTIME"
    return os.getenv(
        specific_key,
        os.getenv("MODEL_RUNTIME_MODE", DEFAULT_RUNTIME_MODE),
    ).strip().lower()


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


def _embedded_is_available(model_type: str) -> bool:
    return model_type in {"land", "house", "rental"}


def _predict_via_http_with_embedded_fallback(
    model_type: str,
    endpoint_url: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Call a remote model service, falling back to the embedded model on failure."""
    try:
        return predict_via_http(model_type, endpoint_url, payload)
    except Exception as remote_error:
        if not _embedded_is_available(model_type):
            raise
        print(
            f"Remote prediction failed for '{model_type}' at {endpoint_url}: {remote_error}. "
            "Falling back to the embedded model."
        )
        return _predict_with_embedded_model(model_type, payload)


def predict_with_active_model(
    db: Session,
    model_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a prediction against the active registered model, falling back to the
    embedded ML packages in ``ml/`` when no HTTP endpoint is reachable.
    """
    from backend.admin.services import get_active_model_by_type

    model_type = (model_type or "").strip().lower()
    endpoint_url = _env_endpoint_for(model_type)

    if endpoint_url:
        if _is_embedded_endpoint(endpoint_url, model_type):
            return _predict_with_embedded_model(model_type, payload)
        return _predict_via_http_with_embedded_fallback(model_type, endpoint_url, payload)

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
        return _predict_via_http_with_embedded_fallback(model_type, endpoint_url, payload)

    if _model_runtime_mode(model_type) in EMBEDDED_RUNTIME_MODES:
        return _predict_with_embedded_model(model_type, payload)

    env_key = MODEL_ENDPOINT_ENV_VARS.get(model_type, f"{model_type.upper()}_MODEL_API_URL")
    raise ValueError(
        f"No model service endpoint is configured for '{model_type}'. "
        f"Run the {model_type} ML service locally and set {env_key}, "
        "or register an active model endpoint in the admin model registry."
    )
