from backend.core.cache_service import get_future_predictions, get_cached_sentiment, get_current_prices

def lstm_forecast(property_type, location, horizon=6):
    return {"trend": "increasing", "values": [100,120,140]}

def sentiment_analysis(property_type, location):
    return {"score": 0.7, "trend": "positive"}

def rl_decision(forecast, sentiment):
    return {"action": "BUY", "confidence": 0.85}    