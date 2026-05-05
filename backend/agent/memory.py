from backend.core.redis_client import get_redis
import json
AGENT_KEY = "agent_sessions"

def save(session_id, data):
    redis_client = get_redis()
    if redis_client is None:
        return
    redis_client.set(session_id, json.dumps(data))

def load(session_id):
    redis_client = get_redis()
    if redis_client is None:
        return 
    data = redis_client.get(session_id)
    return json.loads(data) if data else {}