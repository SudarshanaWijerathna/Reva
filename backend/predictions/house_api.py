"""
House model prediction adapter.
Calls an externally deployed inference API.
"""

import os
from typing import Any, Dict

from backend.predictions.external_model_api import predict_via_http


def predict_house_price(payload: Dict[str, Any]) -> Dict[str, Any]:
    endpoint_url = os.getenv("HOUSE_MODEL_API_URL", "").strip()
    return predict_via_http("house", endpoint_url, payload)
