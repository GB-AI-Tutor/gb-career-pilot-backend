# src/routers/universities.py

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import os
from supabase import create_client, Client
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path
# from src.database import supabase
env_path = Path(__file__).resolve().parent.parent.parent / ".env"

# 2. Load the .env file explicitly
load_dotenv(dotenv_path=env_path)

router = APIRouter()


# getting Supabase
@lru_cache
def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    print(url)
    print("*******************")
    print(key)
    if not url or not key:
        print("❌ ERROR: Supabase environment variables are MISSING!")
    else:
        print(f"✅ Supabase URL found: {url[:10]}...") # Only print first 10 chars for security
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )

@router.get("/api/universities")
async def get_all_universities():
    # This is the actual call to Supabase!
    supabase: Client = Depends(get_supabase_client)
    response = supabase.table("universities").select("*").execute()
    return response.data


@router.get("/universities")
async def get_universities(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    supabase: Client = Depends(get_supabase_client)
):
    try:
        response = (
            supabase.table("universities")
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )

        return {
            "data": response.data,
            "count": len(response.data),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supabase-ping")
async def ping_supabase(supabase: Client = Depends(get_supabase_client)):
    try:
        # This checks the health of the Supabase PostgREST server
        # It doesn't query a table; it just asks the server if it's awake.
        response = supabase.auth.get_session() 
        return {"status": "Supabase Connection Healthy", "details": "Auth service responded."}
    except Exception as e:
        return {"status": "Supabase Connection Failed", "error": str(e)}
        
@router.get("/universities/search")
async def search_universities(
    name: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    supabase: Client = Depends(get_supabase_client)
):
    try:
        query = supabase.table("universities").select("*")

        if name:
            # ilike allows for case-insensitive partial matches (e.g., 'Fast' matches 'FAST NUCES')
            query = query.ilike("name", f"%{name}%") 
        if city:
            query = query.eq("city", city)
        if country:
            # Use .eq() for text. .lte() only works on numbers
            query = query.eq("country", country) 

        response = query.execute()
        return {
            "data": response.data,
            "count": len(response.data),
            "filters": {"name": name, "city": city, "country": country},
        }
    except Exception as e:
        # This will print the exact reason for failure in your Railway logs
        print(f"🔥 Supabase Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
