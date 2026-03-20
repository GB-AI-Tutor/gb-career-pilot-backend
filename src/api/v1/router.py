from fastapi import APIRouter

from src.api.v1.endpoints import ai_endpoints, auth, universities, users

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
