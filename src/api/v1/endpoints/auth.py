import logging
from datetime import UTC, datetime, timedelta

import jwt
import resend
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jwt import InvalidTokenError as JWTError
from loguru import logger

from src.api.v1.deps import get_current_user
from src.config import settings
from src.database import database
from src.database.database import get_supabase_admin_client
from src.rate_limiter import limiter
from src.schemas.users import ForgotPasswordRequest, UserLogin
from src.utils.security import (
    create_access_token,
    create_refresh_access_token,
    decode_jwt_token,
    verify_password,
)

load_dotenv()

router = APIRouter()


# Resend for testing domain using 1 year free domain
# later we can convert it to something else
def send_verification_email(receiver_email: str, token: str):
    verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"

    resend.api_key = settings.RESEND_API_KEY

    try:
        resend.Emails.send(
            {
                "from": "GB Career Pilot <no-reply@raqeebs.app>",
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
@limiter.limit("5/minute")
def login_user(request: Request, body: UserLogin):
    client = database.get_supabase_client()

    exist = (
        client.table("users").select("id", "email", "password").eq("email", body.email).execute()
    )

    # hash_passoword = get_password_hash(body.password)
    if not exist.data:
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
    expires_date = datetime.now(UTC) + timedelta(hours=settings.ACCESS_TOKEN_TIME)

    refresh_token_expires_date = datetime.now(UTC) + timedelta(
        days=settings.REFRESH_ACCESS_TOKEN_TIME
    )

    # generating JWT token- this is for short time
    access_token = create_access_token(user_data, expires_date)

    #  Long lived refresh token
    refresh_token = create_refresh_access_token(user_data, refresh_token_expires_date)
    client.table("users").update({"refresh_token": refresh_token}).eq(
        "id", response["id"]
    ).execute()

    return {"access_token": access_token, "refresh_token": refresh_token, "Token_type": "bearer"}


@router.post("/refresh")
def refresh_access_token(refresh_token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=" Could not validate the refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        data = payload.get("user_data")
        user_id = data.get("sub")

        email = payload.get("email")

    except JWTError as e:
        raise credentials_exception from e

    # checking user still exist
    client = database.get_supabase_client()
    response = (
        client.table("users").select("id", "refresh_token").eq("id", user_id).single().execute()
    )

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=" Student account not found"
        )
    refresh_token_db = response.data.get("refresh_token")

    if refresh_token != refresh_token_db:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=" User logout or refresh token time expired",
        )

    expire = datetime.now(UTC) + timedelta(hours=settings.ACCESS_TOKEN_TIME)
    new_access_token = create_access_token({"sub": user_id, "email": email}, expire)

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
def logout_user(current_user: dict = Depends(get_current_user)):
    client = database.get_supabase_client()
    client.table("users").update({"refresh_token": None}).eq("id", current_user["id"]).execute()
    return {"Message": " Log out successfully."}


@router.post("/forgot-password")
@limiter.limit("3/minute")  # Very strict limit to prevent spam emails
def forgot_password(request: Request, body: ForgotPasswordRequest):
    db = get_supabase_admin_client()

    try:
        # Supabase automatically generates the secure token and sends the email!
        db.auth.reset_password_for_email(
            body.email,
            # This is where the student is sent after clicking the link in their email
            {"redirect_to": "http://localhost:5173/update-password"},
        )
    except Exception as e:
        # We log the real error for to debug later
        logger.warning(f"Password reset email failed for {body.email}: {str(e)}")
        # But we DO NOT raise an HTTPException to the user

    # We return perfectly secure message no matter what happened above
    return {"Detail": "A reset link has been sent to this email if it exists."}
