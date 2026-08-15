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


def _user_id_of(user) -> int | None:
    if isinstance(user, dict):
        return user.get("id")
    return getattr(user, "id", None)


def _recommendation_key(user_id) -> str:
    """
    Per-user cache key.

    The RL state vector includes the caller's held-property counts, so a single
    global entry is wrong by construction - it serves one user's recommendation to
    everyone, and a value cached before a signal fix outlives that fix.
    """
    return f"{RECCOMMENDATION_CACHE_KEY}:{user_id}"


def _compute_market_sentiment():
    # Import lazily so the backend can start even when sentiment services are optional.
    try:
        from Sentiment.Analysis.sentiment_aggregate.agg_pipe import get_market_sentiment
        print("Computing market sentiment...")
        return get_market_sentiment()
    except Exception as exc:
        logger.warning("Failed to compute live market sentiment, using neutral fallback: %s", exc)
        return {
            "housing": {"short_term": {"value": 0.0}, "medium_term": {"value": 0.0}, "long_term": {"value": 0.0}},
            "land": {"short_term": {"value": 0.0}, "medium_term": {"value": 0.0}, "long_term": {"value": 0.0}},
            "rental": {"short_term": {"value": 0.0}, "medium_term": {"value": 0.0}, "long_term": {"value": 0.0}},
        }


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
    try:
        from backend.predictions.current_prices import web_scraper
        result = web_scraper()
    except Exception as exc:
        logger.warning("Failed to scrape current prices: %s", exc)
        result = {
            "sales": {"national average": 15000000.0},
            "rentals": {"national average": 85000.0},
        }

    if redis_client is not None and result:
        try:
            redis_client.set(CURRENT_PRICES_KEY, json.dumps(result))
        except RedisError as exc:
            logger.warning("Failed to update current prices cache: %s", exc)
    return result

def get_current_prices():
    redis_client = get_redis()
    if redis_client is not None:
        try:
            cached_value = redis_client.get(CURRENT_PRICES_KEY)
            if cached_value:
                print("Current prices cache hit")
                return json.loads(cached_value)
        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read current prices cache: %s", exc)

    return update_current_prices() or {}

def compute_future_predictions():
    """
    Snapshot the market index: the latest published value, the forecast path, and
    the metadata a consumer needs to decide whether to trust either.

    ``latest_index`` matters as much as the forecast. Growth factors must be taken
    against the last *published* value, not against the first forecast - anchoring
    on the forecast hides the model's single largest error, the jump from the last
    actual into step one.

    Values are index points (CBSL Asking Price Index, 2019=100), not prices. Only
    ratios within one series are meaningful.
    """
    print("Computing future predictions...")
    from backend.predictions.LSTM.Land import predict as land_index
    from backend.predictions.LSTM.Housing import predict as housing_index
    from backend.predictions.LSTM.Rental import predict as rental_index
    from backend.predictions.LSTM import index_model

    modules = {"land": land_index, "housing": housing_index, "rental": rental_index}
    predictions = {}

    for name, module in modules.items():
        entry = {}
        try:
            manifest = index_model.load_manifest(index_model.resolve_series(name))
            latest = module.latest_index_value()
            path = module.predict_future_sequence_raw(steps=5)

            entry = {
                "next_close": index_model.format_value(path[0]),
                "next_5_close": [index_model.format_value(value) for value in path],
                "latest_index": latest,
                "forecast_path": path,
                "series_end": manifest.get("series_end"),
                "staleness_months": module.staleness_months(),
                "max_plausible_monthly_move": manifest.get("max_plausible_monthly_move"),
                "is_proxy": bool(index_model.load_manifest(name).get("is_proxy", False)),
                "units": "index",
            }
        except Exception as exc:
            # A failed series must not take the whole snapshot down; consumers
            # degrade to a flat path when the forecast is absent.
            logger.warning("Index forecast failed for '%s': %s", name, exc)
            entry = {"error": f"{type(exc).__name__}: {exc}", "units": "index"}

        predictions[name] = entry

    predictions["updated_at"] = datetime.utcnow().isoformat() + "Z"
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

def update_reccomendations(user=None, db=None):
    """Recompute and cache one user's recommendation."""
    user_id = _user_id_of(user)
    if user_id is None or db is None:
        # Falling back to an empty user produced a recommendation for a phantom
        # portfolio and cached it for everyone. There is no user-independent
        # recommendation to compute, so decline rather than invent one.
        logger.warning("update_reccomendations() requires a user with an id and a db session.")
        return {}

    recommendations = {}
    try:
        from backend.rl.recommendation_api import get_recommendation_for_user
        recommendations = get_recommendation_for_user({"id": user_id}, db)
    except Exception as exc:
        logger.warning("Failed to compute recommendations for user %s: %s", user_id, exc)
        return {}

    redis_client = get_redis()
    if redis_client is not None and recommendations:
        try:
            redis_client.set(_recommendation_key(user_id), json.dumps(recommendations))
        except RedisError as exc:
            logger.warning("Failed to update recommendations cache: %s", exc)

    return recommendations

def get_reccomendations(user=None, db=None):
    """Read one user's cached recommendation, recomputing it on a miss."""
    user_id = _user_id_of(user)
    if user_id is None:
        logger.debug("get_reccomendations() called without a user; nothing to return.")
        return {}

    redis_client = get_redis()
    if redis_client is not None:
        try:
            cached_value = redis_client.get(_recommendation_key(user_id))
            if cached_value:
                return json.loads(cached_value)
        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read recommendations cache: %s", exc)

    return update_reccomendations(user, db)