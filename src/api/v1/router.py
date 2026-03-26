from fastapi import APIRouter

# src/core/rate_limit.py (or src/rate_limit.py)
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.v1.endpoints import ai_endpoints, auth, stats, universities, users

# Define it here once!
limiter = Limiter(key_func=get_remote_address)
api_router = APIRouter()

# api_router.include_router(
#     universities.router,
#     prefix="/universities",
#     tags['Universities']

# )

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(universities.router, prefix="/universities", tags=["universities"])
api_router.include_router(ai_endpoints.router, prefix="/groq", tags=["Groq"])
api_router.include_router(stats.router, prefix="/stats", tags=["Stats"])
