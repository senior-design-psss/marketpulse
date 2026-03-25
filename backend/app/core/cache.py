import functools
import hashlib
import json
from typing import Any

from app.core.redis import get_redis


def cached(ttl: int = 300, prefix: str = ""):
    """Cache decorator for async functions. TTL in seconds."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Build cache key from function name + args
            key_data = f"{func.__module__}.{func.__name__}:{args[1:]}:{kwargs}"
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            cache_key = f"cache:{prefix or func.__name__}:{key_hash}"

            try:
                redis = await get_redis()
                cached_value = await redis.get(cache_key)
                if cached_value is not None:
                    return json.loads(cached_value)
            except Exception:
                # If Redis is down, skip cache
                pass

            result = await func(*args, **kwargs)

            try:
                redis = await get_redis()
                await redis.setex(cache_key, ttl, json.dumps(result, default=str))
            except Exception:
                pass

            return result

        return wrapper

    return decorator
