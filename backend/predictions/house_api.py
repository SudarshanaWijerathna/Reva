"""
House model prediction adapter.
Calls an externally deployed inference API.
"""

import os
from typing import Any, Dict

from backend.predictions.external_model_api import predict_via_http


def predict_house_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    endpoint_url = os.getenv("HOUSE_MODEL_API_URL", "").strip()
    if endpoint_url:
        return predict_via_http("house", endpoint_url, payload)

    runtime_mode = os.getenv("HOUSE_MODEL_RUNTIME", "service").strip().lower()
    if runtime_mode in {"embedded", "inprocess", "in-process", "local"}:
        from ml.house_service.service import predict_house_price as predict_local_house_price

        return predict_local_house_price(payload)

    raise ValueError(
        "HOUSE_MODEL_API_URL is not configured. "
        "Run ml.house_service.app locally or deploy it separately and set HOUSE_MODEL_API_URL."
    )
