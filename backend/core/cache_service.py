import json
import logging
from datetime import datetime
import json
from redis.exceptions import RedisError
from backend.core.redis_client import get_redis

MAX_DAYS = 30
HISTORY_KEY = "sentiment_history"
CACHE_KEY = "market_sentiment"
logger = logging.getLogger(__name__)


def _compute_market_sentiment():
    # Import lazily so the backend can start even when sentiment services are optional.
    from Sentiment.Analysis.sentiment_aggregate.agg_pipe import get_market_sentiment
    print("Computing market sentiment...")
    return get_market_sentiment()


def _write_cache(score):
    redis_client = get_redis()
    if redis_client is None:
        return

    try:
        redis_client.set(CACHE_KEY, json.dumps(score))
    except RedisError as exc:
        logger.warning("Failed to write sentiment cache to Redis: %s", exc)


def update_sentiment_cache(test: bool = False):
    score = _compute_market_sentiment()
    his = update_sentiment_history(score)
    curr = _write_cache(score)
    if test:
        print(f"Updated sentiment cache with score:{score}, history record: {his}, cache write result: {curr}")
    return score, his, curr

def is_valid_sentiment(data: dict) -> bool:
    try:
        for sector in data.values():  # land, housing, rental
            for term in sector.values():  # short, medium, long
                if term["value"] != 0.0:
                    return True   # at least one real signal
        return False  # all zeros → invalid

    except (TypeError, KeyError):
        return False


def get_cached_sentiment(force_refresh: bool = False):
    redis_client = get_redis()

    if not force_refresh and redis_client is not None:
        try:
            cached_value = redis_client.get(CACHE_KEY)
            if cached_value:
                data = json.loads(cached_value)

                if is_valid_sentiment(data):
                    print("✅ Valid cache hit")
                    return data
                else:
                    print("⚠️ Cache invalid (all zeros), recomputing...")

        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read sentiment cache: %s", exc)

    print("🔄 Cache miss, recomputing...")
    score = _compute_market_sentiment()
    _write_cache(score)
    return score

def update_sentiment_history(score: dict = None):
    """
    Compute today's sentiment and store it in a rolling 30-day history.
    Does NOT affect existing cache functions.
    """
    redis_client = get_redis()
    if redis_client is None:
        return

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

        return record

    except RedisError as exc:
        logger.warning("Failed to update sentiment history: %s", exc)

    

def get_sentiment_history():
    redis_client = get_redis()
    if redis_client is None:
        return []

    try:
        records = redis_client.lrange(HISTORY_KEY, 0, -1)
        return [json.loads(r) for r in records]

    except (RedisError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read sentiment history: %s", exc)
        return []