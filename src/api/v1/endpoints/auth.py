import logging
from datetime import UTC, datetime, timedelta

import jwt
import resend
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status

from src.config import settings
from src.database import database
from src.schemas.users import UserLogin
from src.utils.security import (
    create_access_token,
    decode_jwt_token,
    verify_password,
)

load_dotenv()

router = APIRouter()


# Resend for testing domain using 1 year free domain
# later we can convert it to something else
def send_verification_email(receiver_email: str, token: str):
    verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"

    resend.api_key = settings.RESEND_API_KEY  # add this to your .env

    try:
        resend.Emails.send(
            {
                "from": "GB Career Pilot <no-reply@raqeebs.app>",  # free no-domain sender
                "to": [receiver_email],
                "subject": "Verify your account",
                "text": f"Welcome! Please click the following link to verify your email:\n\n{verification_link}",
            }
        )
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification mail") from e


@router.post("/verify")
def verify_registration(token: str):
    """Endpoint hit by the React frontend when the user clicks the email link."""
    # Ensure this client uses the SERVICE_ROLE_KEY to bypass RLS during insert
    client = database.get_supabase_admin_client()

    try:
        # 1. Decode token. Automatically throws error if expired or tampered with.
        user_data = decode_jwt_token(token)

        # 2. Finally, insert the verified data into Supabase
        client.table("users").insert(user_data).execute()
        return {"message": "Email verified and account created successfully!"}

    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please register again.",
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification link."
        ) from e
    except Exception as e:
        # Handles database errors (e.g., email already exists if they click twice)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Database error: {str(e)}"
        ) from e


# Login endpoint
@router.post("/login")
def login_user(body: UserLogin):
    client = database.get_supabase_admin_client()

    exist = (
        client.table("users").select("id", "email", "password").eq("email", body.email).execute()
    )

    # hash_passoword = get_password_hash(body.password)
    if not exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with {body.email} email not found. Kindly register first.",
        )
    response = exist.data[0]
    password = response["password"]

    is_valid = verify_password(body.password, password)

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=" wrong password")
    user_data = {
        "sub": str(response["id"]),
        "email": (response["email"]),
    }
    expires_date = datetime.now(UTC) + timedelta(hours=10)

    # generating JWT token
    access_token = create_access_token(user_data, expires_date)

    return {"access_token": access_token, "Token_type": "bearer"}
