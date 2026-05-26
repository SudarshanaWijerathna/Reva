from backend.core.cache_service import get_cached_sentiment

def get_sentiment(property_type):
    sentiment = get_cached_sentiment()
    if not sentiment:
        return {"error": "No sentiment data available"}
    property_sentiment = sentiment.get(property_type, {})

    return property_sentiment if property_sentiment else {"error": f"No sentiment data for {property_type}"}
