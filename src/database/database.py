from dotenv import load_dotenv
from supabase.client import AsyncClient, create_async_client

from src.config import settings

load_dotenv()


async def get_supabase_client() -> AsyncClient:
    """Get cached Supabase client"""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_KEY
    if not url or not key:
        raise ValueError("Missing Supabase credentials")

    return await create_async_client(url, key)


async def get_supabase_admin_client() -> AsyncClient:
    return await create_async_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
