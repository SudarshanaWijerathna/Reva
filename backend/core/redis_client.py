import os
import redis
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_redis():
    global _client

    if _client is not None:
        return _client

    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        print("No REDIS_URL found")
        return None

    _client = redis.from_url(redis_url, decode_responses=True)
    return _client