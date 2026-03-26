"""Redis cache client for GB Career Pilot."""

from loguru import logger
from upstash_redis import Redis

from src.config import settings


class RedisClient:
    """Wrapper for Upstash Redis client with connection testing."""

    def __init__(self):
        """Initialize Redis client."""
        self.client = None
        self._connect()

    def _connect(self):
        """Connect to Upstash Redis."""
        try:
            self.client = Redis(url=settings.UPSTASH_REDIS_URL, token=settings.UPSTASH_REDIS_TOKEN)
            logger.info("✅ Redis client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis client: {e}")
            self.client = None

    def ping(self):
        """Test Redis connection."""
        try:
            if self.client:
                result = self.client.ping()
                logger.info(f"✅ Redis PING successful: {result}")
                return True
            else:
                logger.warning("⚠️ Redis client not initialized")
                return False
        except Exception as e:
            logger.error(f"❌ Redis PING failed: {e}")
            return False

    def get(self, key: str):
        """Get value from Redis."""
        try:
            if self.client:
                return self.client.get(key)
            return None
        except Exception as e:
            logger.error(f"❌ Redis GET failed for key '{key}': {e}")
            return None

    def set(self, key: str, value: str):
        """Set value in Redis."""
        try:
            if self.client:
                return self.client.set(key, value)
            return None
        except Exception as e:
            logger.error(f"❌ Redis SET failed for key '{key}': {e}")
            return None

    def setex(self, key: str, seconds: int, value: str):
        """Set value in Redis with expiration."""
        try:
            if self.client:
                return self.client.setex(key, seconds, value)
            return None
        except Exception as e:
            logger.error(f"❌ Redis SETEX failed for key '{key}': {e}")
            return None

    def delete(self, key: str):
        """Delete key from Redis."""
        try:
            if self.client:
                return self.client.delete(key)
            return None
        except Exception as e:
            logger.error(f"❌ Redis DELETE failed for key '{key}': {e}")
            return None

    def exists(self, key: str):
        """Check if key exists in Redis."""
        try:
            if self.client:
                return self.client.exists(key)
            return False
        except Exception as e:
            logger.error(f"❌ Redis EXISTS failed for key '{key}': {e}")
            return False

    def incr(self, key: str):
        """Increment value in Redis."""
        try:
            if self.client:
                return self.client.incr(key)
            return None
        except Exception as e:
            logger.error(f"❌ Redis INCR failed for key '{key}': {e}")
            return None

    def expire(self, key: str, seconds: int):
        """Set expiration on key."""
        try:
            if self.client:
                return self.client.expire(key, seconds)
            return None
        except Exception as e:
            logger.error(f"❌ Redis EXPIRE failed for key '{key}': {e}")
            return None

    def is_connected(self):
        """Check if Redis is connected."""
        return self.client is not None


def test_redis_connection():
    """Test Redis connection on startup."""
    try:
        redis = RedisClient()
        if redis.is_connected():
            if redis.ping():
                logger.info("✅ Redis connection test PASSED - Ready for caching!")
                return True
            else:
                logger.warning("⚠️ Redis ping failed - Running without cache")
                return False
        else:
            logger.warning("⚠️ Redis client not initialized - Running without cache")
            return False
    except Exception as e:
        logger.error(f"❌ Redis connection test FAILED: {e}")
        logger.warning("⚠️ Application will run without Redis caching")
        return False


# Global Redis client instance
redis_client = RedisClient()


__all__ = ["redis_client", "test_redis_connection", "RedisClient"]
