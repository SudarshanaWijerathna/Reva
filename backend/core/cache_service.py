import json
import logging
from datetime import datetime
from redis.exceptions import RedisError
from backend.core.redis_client import get_redis

MAX_DAYS = 30
HISTORY_KEY = "sentiment_history"
CACHE_KEY = "market_sentiment"
CURRENT_PRICES_KEY = "current_prices"
FUTURE_PREDICTIONS_KEY = "future_predictions"
RECCOMMENDATION_CACHE_KEY = "recommendation_cache"
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
    

def update_current_prices():
    redis_client = get_redis()
    if redis_client is None:
        return

    try:
        from backend.predictions.current_prices import web_scraper
        result = web_scraper()
        redis_client.set(CURRENT_PRICES_KEY, json.dumps(result))
        return result
    except RedisError as exc:
        logger.warning("Failed to update current prices cache: %s", exc)

def get_current_prices():
    redis_client = get_redis()
    if redis_client is None:
        return {}

    try:
        cached_value = redis_client.get(CURRENT_PRICES_KEY)
        if cached_value:
            print("Current prices cache hit")
            return json.loads(cached_value)
        else:
            logger.info("Current prices cache miss")
            fetched = update_current_prices()  # Attempt to refresh cache on miss
            print("Current prices updated")
            return fetched
    except (RedisError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read current prices cache: %s", exc)
        return {}
    
def compute_future_predictions():
    print("Computing future predictions...")
    from backend.predictions.LSTM.Land.predict import (
        predict_next_close_price_from_saved as predict_land_next_close,
        predict_future_sequence_from_saved as predict_land_sequence,
    )
    from backend.predictions.LSTM.Housing.predict import (
        predict_next_close_price_from_saved as predict_housing_next_close,
        predict_future_sequence_from_saved as predict_housing_sequence,
    )
    from backend.predictions.LSTM.Rental.predict import (
        predict_next_close_price_from_saved as predict_rental_next_close,
        predict_future_sequence_from_saved as predict_rental_sequence,
    )

    predictions = {
        "land": {
            "next_close": predict_land_next_close(),
            "next_5_close": predict_land_sequence(steps=5),
        },
        "housing": {
            "next_close": predict_housing_next_close(),
            "next_5_close": predict_housing_sequence(steps=5),
        },
        "rental": {
            "next_close": predict_rental_next_close(),
            "next_5_close": predict_rental_sequence(steps=5),
        },
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }

    return predictions


def update_future_prediction_cache():
    print("Updating future predictions cache...")
    redis_client = get_redis()
    if redis_client is None:
        print("No Redis client available, skipping cache update.")
        return compute_future_predictions()

    try:
        data = compute_future_predictions()
        redis_client.set(FUTURE_PREDICTIONS_KEY, json.dumps(data))
        return data
    except RedisError as exc:
        logger.warning("Failed to update future predictions cache: %s", exc)
        return compute_future_predictions()


def get_future_predictions(force_refresh: bool = False):
    redis_client = get_redis()

    if not force_refresh and redis_client is not None:
        try:
            cached_value = redis_client.get(FUTURE_PREDICTIONS_KEY)
            if cached_value:
                print("Future predictions cache hit")
                return json.loads(cached_value)
        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read future predictions cache: %s", exc)
    print("Future predictions cache miss, recomputing...")
    logger.info("Future predictions cache miss")
    return update_future_prediction_cache()


# Backward-compatible alias using the requested spelling.
def update_future_prediction_catche():
    return update_future_prediction_cache()

def update_reccomendations():
    redis_client = get_redis()
    if redis_client is None:
        return {}

    try:
        from backend.rl.recommendation_api import get_recommendation_for_user
        from backend.auth.routes import user_dependency, Database
        recommendations = get_recommendation_for_user(user_dependency, Database)
        redis_client.set(RECCOMMENDATION_CACHE_KEY, json.dumps(recommendations))
        return recommendations
    except RedisError as exc:
        logger.warning("Failed to update recommendations cache: %s", exc)
        return {}

def get_reccomendations():
    redis_client = get_redis()
    if redis_client is None:
        return {}

    try:
        cached_value = redis_client.get(RECCOMMENDATION_CACHE_KEY)
        if cached_value:
            print("Recommendations cache hit")
            return json.loads(cached_value)
        else:
            logger.info("Recommendations cache miss")
            fetched = update_reccomendations()  # Attempt to refresh cache on miss
            print("Recommendations updated")
            return fetched
    except (RedisError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read recommendations cache: %s", exc)
        return {}