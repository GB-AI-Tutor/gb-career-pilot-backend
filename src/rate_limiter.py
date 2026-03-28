"""Rate limiter configuration for GB Career Pilot API.

Uses SlowAPI with Redis backend for persistent rate limiting across server restarts
and multiple instances.
"""

from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

# Try to use Redis storage, fallback to in-memory if Redis is not available
try:
    from limits.storage import RedisStorage

    from src.config import settings

    redis_url = settings.UPSTASH_REDIS_URL

    # Convert https:// to redis:// for limits library
    if redis_url.startswith("https://"):
        redis_storage_url = redis_url.replace("https://", "redis://")
    else:
        redis_storage_url = redis_url

    # Add token as password for Upstash authentication
    # Format: redis://:token@host
    if "@" not in redis_storage_url:
        # Extract host from redis://host
        host = redis_storage_url.replace("redis://", "")
        redis_storage_url = f"redis://:{settings.UPSTASH_REDIS_TOKEN}@{host}"

    storage = RedisStorage(redis_storage_url)
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=redis_storage_url,
    )
    logger.info("Rate limiter initialized with Redis storage (persistent)")

except Exception as e:
    logger.warning(f"Failed to initialize Redis storage for rate limiter: {e}")
    logger.warning("Falling back to in-memory rate limiting (non-persistent)")

    # Fallback to in-memory storage
    limiter = Limiter(key_func=get_remote_address)
    logger.info("Rate limiter initialized with in-memory storage (resets on restart)")


__all__ = ["limiter"]
