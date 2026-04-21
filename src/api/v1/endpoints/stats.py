# filepath: src/api/v1/endpoints/stats.py
from typing import cast

from fastapi import APIRouter
from postgrest.types import CountMethod

from src.database.database import get_supabase_admin_client

router = APIRouter()


@router.get("/stats")
async def stats():
    db = await get_supabase_admin_client()

    universities = await db.table("universities").select("name").execute()
    uni_names = [uni["name"] for uni in universities.data]

    programs = await db.table("programs").select("name").execute()
    programs_list = []
    for program in programs.data:
        program_name = program["name"]
        programs_list.append(program_name)

    tests = (
        await db.table("tests")
        .select(
            "*",
            count=cast(CountMethod, "exact"),
            head=True,
        )
        .execute()
    )
    questions = (
        await db.table("questions")
        .select(
            "*",
            count=cast(CountMethod, "exact"),
            head=True,
        )
        .execute()
    )

    return {
        "Universities": uni_names,
        "Programs": programs_list,
        "total_tests": tests.count if tests.count else 0,
        "total_questions": questions.count if questions.count else 0,
    }
