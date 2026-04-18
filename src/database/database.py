from dotenv import load_dotenv
from supabase.async_client import AsyncClient
from supabase.client import create_client

from src.config import settings

load_dotenv()


async def get_supabase_client() -> AsyncClient:
    """Get cached Supabase client"""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_KEY
    if not url or not key:
        raise ValueError("Missing Supabase credentials")

    return await create_client(url, key)


async def get_supabase_admin_client() -> AsyncClient:
    return await create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
