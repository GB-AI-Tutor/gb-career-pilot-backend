from fastapi import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.v1.endpoints import (
    ai_endpoints,
    auth,
    report_issues,
    stats,
    test_endpoints,
    universities,
    users,
)

limiter = Limiter(key_func=get_remote_address)
api_router = APIRouter()


api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(universities.router, prefix="/universities", tags=["universities"])
api_router.include_router(report_issues.router, tags=["Report Issues"])
api_router.include_router(ai_endpoints.router, prefix="/groq", tags=["Groq"])
api_router.include_router(stats.router, prefix="/stats", tags=["Stats"])
api_router.include_router(test_endpoints.router, tags=["Test & Exam Prep"])
