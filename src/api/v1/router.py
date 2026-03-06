from fastapi import APIRouter

from src.api.v1.endpoints import users

api_router = APIRouter()

# api_router.include_router(
#     universities.router,
#     prefix="/universities",
#     tags['Universities']

# )

api_router.include_router(users.router, prefix="/users", tags=["users"])
