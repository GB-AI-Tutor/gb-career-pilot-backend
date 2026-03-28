import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.v1.deps import get_current_user
from src.api.v1.endpoints.auth import send_verification_email
from src.database import database
from src.rate_limiter import limiter
from src.schemas.users import UserRegister, UserUpdate
from src.utils.security import create_access_token, get_password_hash

router = APIRouter()


@router.post("/Registeration")
@limiter.limit("5/minute")
def register_user(request: Request, body: UserRegister):
    client = database.get_supabase_client()

    # handling duplicate emails
    existing_user = client.table("users").select("email").eq("email", body.email).execute()

    if existing_user.data:
        # 409 Conflict is the industry standard for duplicate data
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email is already registered.",
        )

    secure_hash = get_password_hash(body.password_hash)

    # Custom auth
    new_id = str(uuid.uuid4())
    user_data = {
        "id": new_id,
        "password": secure_hash,
        **body.model_dump(exclude={"password_hash"}),
    }

    # Generating JWT token
    exp = datetime.now(UTC) + timedelta(minutes=15)

    token = create_access_token(user_data, exp)

    send_verification_email(body.email, token)

    return {"Message": " Verification mail has been send.", **user_data}


@router.get("/me")
def current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user


# for update, user first should be login.
@router.put("/update_user_info")
def update_user_date(body: UserUpdate, current_user: dict = Depends(get_current_user)):
    data = body.model_dump(exclude_none=True)
    client = database.get_supabase_client()

    client.table("users").update(data).eq("id", current_user["id"]).execute()
    return {"Detail": "Data Updated Successfully", "data": data}
    # first we check such user exist
