# src/routers/universities.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
from supabase import create_client, Client

router = APIRouter()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

@router.get("/universities")
async def get_universities(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get list of universities with pagination"""
    try:
        response = supabase.table('universities') \
            .select('*') \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "data": response.data,
            "count": len(response.data),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/universities/search")
async def search_universities(
    name: Optional[str] = None,
    city: Optional[str] = None,
    max_cost: Optional[int] = None
):
    """Search universities by criteria"""
    try:
        query = supabase.table('universities').select('*')
        
        if name:
            query = query.eq('name', name)
        if city:
            query = query.eq('city', city)
        if max_cost:
            query = query.lte('tuition_fee', max_cost)
        
        response = query.execute()
        
        return {
            "data": response.data,
            "count": len(response.data),
            "filters": {
                "name": name,
                "city": city,
                "max_cost": max_cost
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))