import math
from enum import Enum

from fastapi import APIRouter, HTTPException, status
from postgrest.types import CountMethod

from src.database.database import get_supabase_admin_client
from src.schemas.universities import UniversityCreate, UniversityUpdate

router = APIRouter()


class UniversitySortField(str, Enum):
    fee_per_semester = "fee_per_semester"
    ranking_national = "ranking_national"
    has_hostel = "hos_hostel"


@router.post("/Add_university")
def add_university(body: UniversityCreate):
    client = get_supabase_admin_client()
    data = body.model_dump(mode="json")

    name = client.table("universities").select("*").eq("name", data.get("name")).execute()

    if name.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=" University already exist"
        )

    client.table("universities").insert(data).execute()

    return {"Detail": " University added successfully"}


@router.patch("/update_university/{name}")
def update_university(name: str, body: UniversityUpdate):
    client = get_supabase_admin_client()

    user = client.table("universities").select("*").eq("name", name).execute()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=" There is not such universiy"
        )

    data = body.model_dump(exclude_none=True, mode="json")

    client.table("universities").update(data).eq("name", name).execute()

    return {"Detail": f" Data of universitie :{name} updated successfully"}


@router.delete("/delete_universitiy")
def delete_university(name: str):
    client = get_supabase_admin_client()
    user = client.table("universities").select("*").eq("name", name).execute()

    if not user.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=" No such university found"
        )

    client.table("universities").delete().eq("name", name).execute()

    return {"Detail": "University record deleted successfully"}


@router.get("/get_university")
def get_universities(
    limit: int = 10,
    offset: int = 0,
    sort_by: UniversitySortField = UniversitySortField.ranking_national,
    order: str = "asc",
):
    is_desc = order.lower() == "desc"
    range_end = offset + limit - 1
    client = get_supabase_admin_client()
    try:
        query = (
            client.table("universities")
            .select("*", count=CountMethod.exact)
            .order(sort_by.value, desc=is_desc)
            .range(offset, range_end)
            .execute()
        )

        total_count = query.count or 0
        total_pages = math.ceil(total_count / limit)

        return {
            "data": query.data,
            "metadata": {
                "total_count": total_count,
                "total_pages": total_pages,
                "limit": limit,
                "offset": offset,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/get_university_by_name")
def get_university_by_name(name: str):
    client = get_supabase_admin_client()

    university = client.table("universities").select("").eq("name", name.lower()).execute()
    print("*" * 20)
    print(university.data)
    print("*" * 20)

    if not university.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such university exist"
        )
    uni_id = university.data[0]["id"]

    programs = client.table("programs").select("*").eq("university_id", uni_id).execute()
    programs_data = programs.model_dump()
    program_data = programs_data["data"]

    print(program_data[0]["id"])

    for i in range(0, len(program_data)):
        admission_requirement = (
            client.table("admission_requirements")
            .select(
                "matric_weightage,fsc_weightage,test_weightage,last_closing_aggregate,quota_category"
            )
            .eq("program_id", program_data[i]["id"])
            .execute()
        )
        dump = admission_requirement.model_dump()["data"]
        program_data[i]["admission_requirement"] = dump

    return {"University": university.data, "Programs:": program_data}


@router.get("/univeristy/{id}/programs")
def programs_by_university(id: int, field: str):
    client = get_supabase_admin_client()

    programs = client.table("programs").select("*").eq("university_id", id).execute()
    programs_data = programs.model_dump()
    program_data = programs_data["data"]

    print(program_data[0]["id"])

    for i in range(0, len(program_data)):
        admission_requirement = (
            client.table("admission_requirements")
            .select(
                "matric_weightage,fsc_weightage,test_weightage,last_closing_aggregate,quota_category"
            )
            .eq("program_id", program_data[i]["id"])
            .execute()
        )
        dump = admission_requirement.model_dump()["data"]
        program_data[i]["admission_requirement"] = dump

    return {"Programs": program_data}
