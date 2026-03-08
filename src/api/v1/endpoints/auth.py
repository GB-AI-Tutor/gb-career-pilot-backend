import logging
import smtplib
import uuid
from datetime import UTC, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status

from src.config import settings
from src.database import database
from src.schemas.users import UserRegister
from src.utils.security import get_password_hash

load_dotenv()

router = APIRouter()


def send_verification_email(receiver_email: str, token: str):
    verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"

    # Build the email
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify your account - GB Career Pilot"
    message["From"] = settings.PROJECT_EMAIL
    message["To"] = receiver_email

    text_content = f"Welcome! Click the link below to verify your email:\n\n{verification_link}"
    message.attach(MIMEText(text_content, "plain"))

    # Send via Gmail SMTP
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()  # encrypts the connection
            server.ehlo()
            server.login(settings.PROJECT_EMAIL, settings.EMAIL_APP_PASSWORD)
            server.sendmail(settings.PROJECT_EMAIL, receiver_email, message.as_string())

    except smtplib.SMTPException as e:
        logging.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification mail") from e


# #Resend for testing domain
# def send_verification_email(receiver_email: str, token: str):
#     verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"

#     resend.api_key = settings.RESEND_API_KEY  # add this to your .env

#     try:
#         resend.Emails.send(
#             {
#                 "from": "GB Career Pilot <onboarding@resend.dev>",  # free no-domain sender
#                 "to": [receiver_email],
#                 "subject": "Verify your account",
#                 "text": f"Welcome! Please click the following link to verify your email:\n\n{verification_link}",
#             }
#         )
#     except Exception as e:
#         logging.error(f"Failed to send email: {e}")
#         raise HTTPException(status_code=500, detail="Failed to send verification mail") from e

#     # def send_verification_email(receiver_email: str, token: str):
#     #     verification_link = f"{settings.FRONTEND_URL}/verify?token={token}"

#     #     configuration = sib_api_v3_sdk.Configuration()
#     #     configuration.api_key["api-key"] = settings.BREVO_API

#     #     api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

#     #     send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
#     #         to=[{"email": receiver_email}],
#     #         sender={"name": "GB Career Pilot", "email": settings.PROJECT_EMAIL},
#     #         subject="Verify your account",
#     #         text_content=f"Welcome! Please click the following link to verify your email and complete your registration:\n\n{verification_link}",
#     #     )

#     # try:
#     #     api_instance.send_transac_email(send_smtp_email)
#     # except ApiException as e:
#     #     logging.error(f"Failed to send email: {e}")
#     #     raise HTTPException(status_code=500, detail="Failed to send verification mail") from e


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


# @router.post("/login")
# def login_user():
#     pass
