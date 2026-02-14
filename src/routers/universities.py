# src/routers/universities.py

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import os
from supabase import create_client, Client
from functools import lru_cache

router = APIRouter()


@lru_cache
def get_supabase_client() -> Client:
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )


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
            query = query.eq("name", name)
        if city:
            query = query.eq("city", city)
        if max_cost:
            query = query.lte("country", country)

        response = query.execute()

        return {
            "data": response.data,
            "count": len(response.data),
            "filters": {
                "name": name,
                "city": city,
                "country": country,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
