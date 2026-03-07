import smtplib
import uuid
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status

from src.config import settings
from src.database import database
from src.schemas.users import UserRegister
from src.utils.security import get_password_hash
import logging
import traceback

load_dotenv()

router = APIRouter()


def send_verification_email(receiver_email: str, token: str):
    verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"

    msg = EmailMessage()
    msg.set_content(
        f"Welcome! Please click the following link to verify your email and complete your registration:\n\n{verification_link}"
    )
    msg["Subject"] = "Verify your account"
    msg["From"] = settings.PROJECT_EMAIL
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(settings.PROJECT_EMAIL, settings.EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        logging.error(f"Failed to send email to {receiver_email}: {type(e).__name__}: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to send verification mail: {type(e).__name__}: {str(e)}") from e


@router.get("/GetUserData")
def get_users():
    data = database.get_supabase_client()
    response = data.table("users").select("*").execute()
    users = response.data

    return users


@router.post("/Registeration")
def register_user(body: UserRegister):
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

    # user_metadata = body.model_dump(exclude={"password_hash"})

    # through this we add the new user to auth.user : supabase auth
    # auth_response = client.auth.sign_up(
    #     {
    #         "email": body.email,
    #         "password": secure_hash,
    #         "options": {"data": user_metadata},
    #     }
    # )

    # Custom auth
    new_id = str(uuid.uuid4())
    user_data = {
        "id": new_id,
        "password": secure_hash,
        **body.model_dump(exclude={"password_hash"}),
    }

    payload = {"user_data": user_data, "exp": datetime.now(UTC) + timedelta(minutes=15)}

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

    send_verification_email(body.email, token)

    return {"Message": " Verification mail has been send."}

    #     try:
    #         response = (client.table("users").insert(user_data).execute())
    #         print("Success:", response)
    #     except Exception as e:
    #         print(f"Validation or connection error while inserting data : {e}")

    # except AuthApiError as e:
    #     message = str(e).lower()
    #     if "rate limit" in message or "429" in message:
    #         raise HTTPException(
    #             status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    #             detail=" Too many signup attempts. Please try again later",
    #         ) from e
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST, detail=f"Signup failed {str(e)}"
    #     ) from e

    # new_user_id = auth_response.user.id
    # user_data = body.model_dump(exclude={"password_hash"})
    # user_data['id'] = new_user_id
    # response = client.table("users").insert(user_data).execute()
    # return user_data


@router.post("/verify")
def verify_registration(token: str):
    """Endpoint hit by the React frontend when the user clicks the email link."""
    # Ensure this client uses the SERVICE_ROLE_KEY to bypass RLS during insert
    client = database.get_supabase_admin_client()

    try:
        # 1. Decode token. Automatically throws error if expired or tampered with.
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_data = payload.get("user_data")

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


@router.post("/login")
def login_user():
    pass
