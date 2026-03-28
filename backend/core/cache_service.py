import json
import logging

from redis.exceptions import RedisError

from backend.core.redis_client import redis_client


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

