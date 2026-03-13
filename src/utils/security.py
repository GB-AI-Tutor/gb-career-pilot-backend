import hashlib
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from src.config import settings

# pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
# deprecated ="auto" this help in future if we change the hashing from bcrypt to something else by automatcally rehashing old passwords


def get_password_hash(password: str):
    # We pre-hadh it with SHA-256 to ensure any length fits in bcrypt
    # This will convert any password into a 64 chatacter string
    password_bytes = password.encode("utf-8")
    digest = hashlib.sha256(password_bytes).hexdigest().encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(digest, salt)

    # now hash the digest using bcrypt
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")  # this convert to byte format
    digest = hashlib.sha256(password_bytes).hexdigest().encode("utf-8")
    return bcrypt.checkpw(digest, hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_date: datetime):
    payload = {
        "user_data": data,
        # we have to use exp otherwise json will not be able to serialize the datatime
        "exp": expires_date,
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, settings.ALGORITHM)
    return token


def create_refresh_access_token(
    data: dict, expires_date: datetime = datetime.now(UTC) + timedelta(hours=150)
):
    payload = {
        "user_data": data,
        # we have to use exp otherwise json will not be able to serialize the datatime
        "exp": expires_date,
    }

    token = jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, settings.ALGORITHM)
    return token


def decode_jwt_token(token: str) -> dict:
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, [settings.ALGORITHM])
    user = payload.get("user_data")
    return user
