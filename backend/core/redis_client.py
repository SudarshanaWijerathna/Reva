import os

import redis


def _build_redis_client():
    redis_url = (os.getenv("REDIS_URL") or "").strip()
    if redis_url:
        return redis.from_url(redis_url, decode_responses=True)

    redis_host = (os.getenv("REDIS_HOST") or "").strip()
    if not redis_host:
        return None

    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=True,
    )


redis_client = _build_redis_client()
