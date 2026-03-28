from dotenv import load_dotenv
from supabase.client import Client, create_client

from src.config import settings

load_dotenv()


def get_supabase_client() -> Client:
    """Get cached Supabase client"""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_KEY
    if not url or not key:
        raise ValueError("Missing Supabase credentials")

    return create_client(url, key)


def get_supabase_admin_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
