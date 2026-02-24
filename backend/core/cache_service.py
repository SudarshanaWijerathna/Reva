import json
from backend.core.redis_client import redis_client
from Sentiment.Analysis.sentiment_aggregate.agg_pipe import get_market_sentiment


CACHE_KEY = "market_sentiment"

def update_sentiment_cache():
    score = get_market_sentiment()
    redis_client.set(CACHE_KEY, json.dumps(score))
    return score

def get_cached_sentiment():
    cached_value = redis_client.get(CACHE_KEY)
    if cached_value:
        return json.loads(cached_value)
    return None

