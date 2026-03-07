from fastapi import APIRouter, HTTPException, status
from gotrue.errors import AuthApiError

from src.database import database
from src.schemas.users import UserRegister, UserResponse

router = APIRouter()


@router.get("/users")
def get_users():
    data = database.get_supabase_client()
    response = data.table("users").select("*").execute()
    users = response.data

    return users


@router.post("/users", response_model=UserResponse)
def register_user(body: UserRegister):
    client = database.get_supabase_client()
    user_metadata = body.model_dump(exclude={"password_hash"})

    try:
        # through this we add the new user to auth.user
        auth_response = client.auth.sign_up(
            {
                "email": body.email,
                "password": body.password_hash,
                "options": {"data": user_metadata},
            }
        )
    except AuthApiError as e:
        message = str(e).lower()
        if "rate limit" in message or "429" in message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=" Too many signup attempts. Please try again later",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Signup failed {str(e)}"
        ) from e
    if not auth_response or not auth_response.user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup failed: No user returned from auth provider",
        )

    # new_user_id = auth_response.user.id
    # user_data = body.model_dump(exclude={"password_hash"})
    # user_data['id'] = new_user_id
    # response = client.table("users").insert(user_data).execute()

    user_metadata["id"] = auth_response.user.id
    user_metadata["created_at"] = str(auth_response.user.created_at)
    return user_metadata
