# src/core/rate_limit.py (or src/rate_limit.py)
from slowapi import Limiter
from slowapi.util import get_remote_address

# Define it here once!
limiter = Limiter(key_func=get_remote_address)
