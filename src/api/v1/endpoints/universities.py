from fastapi import APIRouter, HTTPException, status

from src.database.database import get_supabase_admin_client
from src.schemas.universities import UniversityCreate, UniversityUpdate

router = APIRouter()


@router.post("/Add_university")
def add_university(body: UniversityCreate):
    client = get_supabase_admin_client()
    data = body.model_dump(mode="json")
    name = client.table("universities").select("*").eq("name", data.get("name")).execute()

    if name:
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
