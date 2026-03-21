from fastapi import APIRouter

from src.database.database import get_supabase_admin_client

router = APIRouter()


@router.get("/stats")
def stats():
    db = get_supabase_admin_client()

    universities = db.table("universities").select("name").execute()
    uni_names = universities.model_dump()["data"]
    programs = db.table("programs").select("name").execute()
    programs_name = programs.model_dump()["data"]

    universities_names = []

    for uni in uni_names:
        universities_names.append(uni["name"])

    programs_list = []
    for pro in programs_name:
        programs_list.append(pro["name"])

    programs_list = set(programs_list)
    return {"Universities": universities_names, "Programs": programs_list}
