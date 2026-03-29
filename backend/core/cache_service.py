import json
import logging
from datetime import datetime
import json
from redis.exceptions import RedisError
from backend.core.redis_client import redis_client

MAX_DAYS = 30
HISTORY_KEY = "sentiment_history"
CACHE_KEY = "market_sentiment"
logger = logging.getLogger(__name__)


def _compute_market_sentiment():
    # Import lazily so the backend can start even when sentiment services are optional.
    from Sentiment.Analysis.sentiment_aggregate.agg_pipe import get_market_sentiment

    return get_market_sentiment()


def _write_cache(score):
    if redis_client is None:
        return

    try:
        redis_client.set(CACHE_KEY, json.dumps(score))
    except RedisError as exc:
        logger.warning("Failed to write sentiment cache to Redis: %s", exc)


def update_sentiment_cache():
    score = _compute_market_sentiment()
    update_sentiment_history(score)
    _write_cache(score)
    return score


def get_cached_sentiment(force_refresh: bool = False):
    if not force_refresh and redis_client is not None:
        try:
            cached_value = redis_client.get(CACHE_KEY)
            if cached_value:
                return json.loads(cached_value)
        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read sentiment cache from Redis: %s", exc)

    score = _compute_market_sentiment()
    _write_cache(score)
    return score

def update_sentiment_history(force_refresh: bool = False, score=None):
    """
    Compute today's sentiment and store it in a rolling 30-day history.
    Does NOT affect existing cache functions.
    """
    if not force_refresh and redis_client is not None:
        try:
            # 1. Compute latest sentiment (reuse your function)
            if score is None:
                score = _compute_market_sentiment()

            # 2. Create record with timestamp
            record = {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "data": score
            }

            # 3. Push to Redis list (left push = newest first)
            redis_client.lpush(HISTORY_KEY, json.dumps(record))

            # 4. Trim list to last 30 days
            redis_client.ltrim(HISTORY_KEY, 0, MAX_DAYS - 1)
            print("Updated sentiment history with record:", record)
            return record

        except RedisError as exc:
            logger.warning("Failed to update sentiment history: %s", exc)
    else:
        print("Redis client not available, skipping history update.")
        return None
    

    

def get_sentiment_history():
    
    try:
        records = redis_client.lrange(HISTORY_KEY, 0, -1)
        return [json.loads(r) for r in records]

    except (RedisError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read sentiment history: %s", exc)
        return []