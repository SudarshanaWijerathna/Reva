from backend.core.cache_service import get_cached_sentiment


PROPERTY_NAME_MAP = {
    "house": "housing",
    "housing": "housing",
    "land": "land",
    "rental": "rental",
}

TERM_NAME_MAP = {
    "short": "short_term",
    "short_term": "short_term",
    "medium": "medium_term",
    "medium_term": "medium_term",
    "long": "long_term",
    "long_term": "long_term",
}


def fetch_market_sentiment(force_refresh: bool = False):
    return get_cached_sentiment(force_refresh=force_refresh)


def get_overall_sentiment(data: dict | None):
    if not data:
        return "unknown"

    values = []
    for prop in ("land", "housing", "rental"):
        prop_data = data.get(prop) or {}
        medium_term = prop_data.get("medium_term") or {}
        value = medium_term.get("value")
        if isinstance(value, (int, float)):
            values.append(float(value))

    if not values:
        return "unknown"

    average_sentiment = sum(values) / len(values)
    if average_sentiment >= 0.2:
        return "bullish"
    if average_sentiment <= -0.2:
        return "bearish"
    return "neutral"


def get_sentiment(data: dict | None, property_type: str, term: str):
    if not data:
        return {"value": 0.0, "label": "unknown"}

    normalized_property = PROPERTY_NAME_MAP.get((property_type or "").strip().lower())
    normalized_term = TERM_NAME_MAP.get((term or "").strip().lower())
    if not normalized_property or not normalized_term:
        return {"value": 0.0, "label": "unknown"}

    result = (data.get(normalized_property) or {}).get(normalized_term)
    if not result:
        return {"value": 0.0, "label": "unknown"}

    return {
        "value": float(result.get("value", 0.0)),
        "label": str(result.get("label", "unknown")),
    }
    





    


    
