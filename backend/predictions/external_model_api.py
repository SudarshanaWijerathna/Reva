"""
Helpers for invoking externally deployed prediction models.
"""

from typing import Any, Dict
import requests


def _extract_prediction_value(response_payload: Dict[str, Any]) -> float:
    """
    Extract a numeric prediction from common response field names.
    """
    candidate_keys = (
        "predicted_value",
        "prediction",
        "price",
        "value",
        "result",
        "estimated_price",
    )
    for key in candidate_keys:
        value = response_payload.get(key)
        if value is not None:
            return float(value)
    raise ValueError(
        "Model response did not contain a supported prediction field. "
        f"Expected one of: {', '.join(candidate_keys)}"
    )


def predict_via_http(model_name: str, endpoint_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call an external model endpoint and normalize the response.
    """
    if not endpoint_url:
        raise ValueError(
            f"{model_name.upper()}_MODEL_API_URL is not configured. "
            f"Set it in environment variables to enable {model_name} predictions."
        )

    try:
        response = requests.post(
            endpoint_url,
            json={"features": payload},
            timeout=45,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"{model_name} model API request failed: {str(exc)}") from exc

    try:
        response_payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{model_name} model API returned non-JSON response") from exc

    prediction_value = _extract_prediction_value(response_payload)
    return {
        "predicted_value": prediction_value,
        "raw_response": response_payload
    }
