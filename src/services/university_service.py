from postgrest.types import CountMethod

from src.database.database import get_supabase_admin_client

client = get_supabase_admin_client()


def get_universities_from_db(
    location: str | None = None, program_name: str | None = None, max_fee: int | None = None
):
    query = client.table("programs").select(
        "*, universities!inner(*), admission_requirements(*)", count=CountMethod.exact
    )

    if location:
        query = query.ilike("universities.city", f"%{location}%")
    if program_name:
        query = query.ilike("name", f"%{program_name}%")
    if max_fee:
        query = query.lte("estimated_total_fee", max_fee)

    result = query.execute()
    return result.data  # This returns a list of dictionaries (the real data!)
