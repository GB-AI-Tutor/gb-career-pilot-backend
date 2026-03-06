from dotenv import load_dotenv
from supabase import Client, create_client

from src.config import settings

load_dotenv()


def get_supabase_client() -> Client:
    """Get cached Supabase client"""
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_KEY
    if not url or not key:
        raise ValueError("Missing Supabase credentials")

    return create_client(url, key)
