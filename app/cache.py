import json
from typing import Optional
from redis import Redis
from redis.exceptions import RedisError
from fastapi.encoders import jsonable_encoder  
from .config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

def _key(user_id: int) -> str:
    return f"chatrooms:{user_id}"

def get_cached_chatrooms(user_id: int) -> Optional[list]:
    try:
        raw = redis_client.get(_key(user_id))
        return json.loads(raw) if raw else None
    except (RedisError, json.JSONDecodeError):
        return None  

def set_cached_chatrooms(user_id: int, data: list, ttl_seconds: int = 600):
    try:
        safe = jsonable_encoder(data)                
        redis_client.setex(_key(user_id), ttl_seconds, json.dumps(safe))
    except RedisError:
        pass

def delete_cached_chatrooms(user_id: int):
    try:
        redis_client.delete(_key(user_id))
    except RedisError:
        pass
