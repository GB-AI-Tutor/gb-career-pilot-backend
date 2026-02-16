# src/routers/auth.py
"""
Authentication router - FIXED VERSION with bcrypt password handling
"""

import os
from datetime import datetime, timedelta
from functools import lru_cache

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, validator
from supabase import Client, create_client

router = APIRouter()

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for token authentication
security = HTTPBearer()


# Supabase client
@lru_cache
def get_supabase_client() -> Client:
    """Get cached Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_PUBLISHABLE_KEY")
        or os.getenv("SUPABASE_KEY")
    )

    if not url or not key:
        raise ValueError("Missing Supabase credentials")

    return create_client(url, key)


# Pydantic models
class UserRegister(BaseModel):
    """User registration request"""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt max is 72 bytes
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str | None = Field(None, max_length=20)

    # Student profile data
    fsc_percentage: float | None = Field(None, ge=0, le=100)
    city: str | None = None
    field_of_interest: str | None = None

    @validator("password")
    def validate_password(cls, v):  # noqa: N805
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 72:
            raise ValueError("Password cannot be longer than 72 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


class UserLogin(BaseModel):
    """User login request"""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""

    access_token: str
    token_type: str = "bearer"
    user: dict


class UserProfile(BaseModel):
    """User profile response"""

    id: int
    email: str
    full_name: str
    phone: str | None
    fsc_percentage: float | None
    city: str | None
    field_of_interest: str | None
    created_at: datetime


# Helper functions
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    Truncates to 72 bytes to avoid bcrypt error
    """
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode("utf-8")[:72]
    return pwd_context.hash(password_bytes.decode("utf-8"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against hash
    Truncates to 72 bytes to match hashing
    """
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = plain_password.encode("utf-8")[:72]
    return pwd_context.verify(password_bytes.decode("utf-8"), hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        ) from err
    except jwt.JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials"
        ) from err


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client),
) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials"
        )

    # Get user from database
    response = supabase.table("users").select("*").eq("id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return response.data[0]


# Routes
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, supabase: Client = Depends(get_supabase_client)):
    """
    Register a new user

    Creates user account and returns JWT token
    """
    try:
        # Check if user already exists
        existing_user = supabase.table("users").select("*").eq("email", user_data.email).execute()

        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )

        # Hash password (with truncation handling)
        hashed_password = hash_password(user_data.password)

        # Create user
        user_dict = {
            "email": user_data.email,
            "password_hash": hashed_password,
            "full_name": user_data.full_name,
            "phone": user_data.phone,
            "fsc_percentage": user_data.fsc_percentage,
            "city": user_data.city,
            "field_of_interest": user_data.field_of_interest,
        }

        response = supabase.table("users").insert(user_dict).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user"
            )

        created_user = response.data[0]

        # Create access token
        access_token = create_access_token(data={"sub": str(created_user["id"])})

        # Remove password hash from response
        user_response = {k: v for k, v in created_user.items() if k != "password_hash"}

        return {"access_token": access_token, "token_type": "bearer", "user": user_response}

    except HTTPException:
        raise
    except Exception as err:
        print(f"Registration error: {str(err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(err)}",
        ) from err


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, supabase: Client = Depends(get_supabase_client)):
    """
    Login user

    Validates credentials and returns JWT token
    """
    try:
        # Get user by email
        response = supabase.table("users").select("*").eq("email", credentials.email).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
            )

        user = response.data[0]

        # Verify password
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
            )

        # Create access token
        access_token = create_access_token(data={"sub": str(user["id"])})

        # Remove password hash from response
        user_response = {k: v for k, v in user.items() if k != "password_hash"}

        return {"access_token": access_token, "token_type": "bearer", "user": user_response}

    except HTTPException:
        raise
    except Exception as err:
        print(f"Login error: {str(err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(err)}",
        ) from err


@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile

    Requires authentication
    """
    # Remove password hash
    user_data = {k: v for k, v in current_user.items() if k != "password_hash"}
    return user_data


@router.put("/me", response_model=UserProfile)
async def update_my_profile(
    full_name: str | None = None,
    phone: str | None = None,
    fsc_percentage: float | None = None,
    city: str | None = None,
    field_of_interest: str | None = None,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    """
    Update current user profile

    Requires authentication
    """
    try:
        # Build update dict
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        if phone is not None:
            update_data["phone"] = phone
        if fsc_percentage is not None:
            update_data["fsc_percentage"] = fsc_percentage
        if city is not None:
            update_data["city"] = city
        if field_of_interest is not None:
            update_data["field_of_interest"] = field_of_interest

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
            )

        # Update user
        response = (
            supabase.table("users").update(update_data).eq("id", current_user["id"]).execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile"
            )

        updated_user = response.data[0]

        # Remove password hash
        user_response = {k: v for k, v in updated_user.items() if k != "password_hash"}

        return user_response

    except HTTPException:
        raise
    except Exception as err:
        print(f"Update profile error: {str(err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(err)}",
        ) from err


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client should delete token)
    """
    return {"message": "Successfully logged out"}
