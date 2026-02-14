# src/routers/universities.py
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import os
from supabase import create_client, Client
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

router = APIRouter()

@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") 
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials")
    
    return create_client(url, key)

# ✅ FIX: Removed /api prefix, use Depends correctly
@router.get("/universities")
async def get_universities(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    supabase: Client = Depends(get_supabase_client)  # ✅ Correct position
):
    """Get universities with pagination"""
    try:
        response = (
            supabase.table("universities")
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )

        # ✅ Return structured response
        return {
            "data": response.data,
            "count": len(response.data),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/universities/search")
async def search_universities(
    name: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    supabase: Client = Depends(get_supabase_client)
):
    """Search universities"""
    try:
        query = supabase.table("universities").select("*")

        if name:
            query = query.ilike("name", f"%{name}%")
        if city:
            query = query.ilike("city", f"%{city}%")
        if country:
            query = query.eq("country", country)

        response = query.execute()
        
        return {
            "data": response.data,
            "count": len(response.data),
            "filters": {"name": name, "city": city, "country": country},
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supabase-ping")
async def ping_supabase(supabase: Client = Depends(get_supabase_client)):
    """Test Supabase connection"""
    try:
        response = supabase.table("universities").select("id").limit(1).execute()
        
        return {
            "status": "connected",
            "message": "Supabase connection healthy",
            "has_data": len(response.data) > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Connection failed: {str(e)}"
        )