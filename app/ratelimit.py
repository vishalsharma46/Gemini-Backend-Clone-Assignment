from datetime import datetime, timedelta
from redis import Redis
from .config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

def today_key(user_id: int) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return f"user:{user_id}:daily_prompts:{today}"

def increment_and_check(user_id: int, limit: int) -> bool:
    key = today_key(user_id)
    val = redis_client.incr(key)
    
    if val == 1:
       
        tomorrow = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        ttl = int((tomorrow - datetime.utcnow()).total_seconds())
        redis_client.expire(key, ttl)
    return val <= limit
