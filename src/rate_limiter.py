"""Rate limiter configuration for GB Career Pilot API.

Uses SlowAPI with in-memory storage for development.
For production with Redis persistence, configure a dedicated Redis instance.
"""

from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

# Use in-memory rate limiting for development
# Note: This resets on server restart, but is reliable and requires no external dependencies
limiter = Limiter(key_func=get_remote_address)
logger.info("Rate limiter initialized with in-memory storage (resets on restart)")


__all__ = ["limiter"]
