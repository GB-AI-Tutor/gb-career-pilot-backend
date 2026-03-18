import math
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from postgrest.types import CountMethod

from src.api.v1.deps import get_current_user
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
    current_user: dict = Depends(get_current_user),
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
def get_university_by_name(name: str, current_user: dict = Depends(get_current_user)):
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


@router.get(
    "/univeristy/{id}/programs",
)
def programs_by_university(id: int, field: str, current_user: dict = Depends(get_current_user)):
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


class Sector(str, Enum):
    Private = ("Private",)
    Public = ("Public",)
    Semi_Government = "Semi-Government"


@router.get("/programs/search")
def search_programs(
    # student_percentage: float | None = None, # 👈 NEW: Optional student marks
    quota_category: str = "Open Merit",  # 👈 NEW: Default to Open Merit
    field: str | None = None,
    city: str | None = None,
    min_fee: int | None = None,
    max_fee: int | None = None,
    sector: Sector = Sector.Private,
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "estimated_total_fee",
    order: str = "asc",
    current_user: dict = Depends(get_current_user),
):
    is_desc = order.lower() == "desc"
    range_end = offset + limit - 1
    student_percentage = current_user["fsc_percentage"]
    client = get_supabase_admin_client()

    try:
        # 1. Base Query with Nested Join
        # Notice we added admission_requirements(*) to grab the cut-offs!
        query = client.table("programs").select(
            "*, universities!inner(*), admission_requirements(*)", count=CountMethod.exact
        )

        # 2. Apply Filters (Same as before)
        if field:
            query = query.ilike("field_of_study", f"%{field}%")
        if min_fee is not None:
            query = query.gte("estimated_total_fee", min_fee)
        if max_fee is not None:
            query = query.lte("estimated_total_fee", max_fee)
        if city:
            query = query.ilike("universities.city", f"%{city}%")
        if sector is not None:
            print("Sectore:", sector.value)
            query = query.eq("universities.sector", sector.value)

        # 3. Apply Sorting and Pagination
        query = query.order(sort_by, desc=is_desc)
        query = query.range(offset, range_end)

        # 4. Execute the query
        response = query.execute()
        programs_data = response.data

        # 5. 🧠 The AI Counselor Logic: Inject Eligibility Tiers
        if student_percentage is not None:
            for program in programs_data:
                # Set a default state
                program["eligibility"] = {"tier": "Unknown", "is_eligible": False}

                # Find the requirement that matches the student's quota
                reqs = program.get("admission_requirements", [])
                target_req = next((r for r in reqs if r["quota_category"] == quota_category), None)

                if target_req:
                    min_fsc = float(target_req["min_fsc_percentage"])
                    merit_cutoff = float(target_req["last_closing_aggregate"])

                    # Apply the Tier Logic
                    if student_percentage < min_fsc:
                        program["eligibility"] = {"tier": "Not Eligible", "is_eligible": False}
                    elif student_percentage > (merit_cutoff + 10):
                        program["eligibility"] = {"tier": "Safety", "is_eligible": True}
                    elif (merit_cutoff - 10) <= student_percentage <= (merit_cutoff + 10):
                        program["eligibility"] = {"tier": "Target", "is_eligible": True}
                    else:
                        program["eligibility"] = {"tier": "Reach", "is_eligible": True}

                # Cleanup: We can delete the raw requirements list to keep the JSON payload small
                del program["admission_requirements"]

        # 6. Calculate Metadata
        total_count = response.count or 0
        total_page = math.ceil(total_count / limit) if limit > 0 else 0

        return {
            "data": programs_data,
            "metadata": {
                "total_count": total_count,
                "total_pages": total_page,
                "limit": limit,
                "offset": offset,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Program search failed: {str(e)}",
        ) from e
