from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Fields(str, Enum):
    computer_science = "Computer Science"
    medical = "Medical"
    engineering = "Engineering"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: str = Field(max_length=11)
    city: str
    field_of_interest: Fields


class UserRegister(UserBase):
    password_hash: str
    fsc_percentage: float = Field(
        gt=0, lt=100, description=" The Percentage should be between 0 and 100"
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None)
    phone: str | None = Field(default=None, max_length=11)
    fsc_percentage: float | None = Field(default=None, gt=0, lt=100)
    city: str | None = Field(default=None)
    field_of_interest: Fields | None = Field(default=None)


class UserResponse(UserBase):
    id: str
    fsc_percentage: float = Field(gt=0, lt=100)
    created_at: str

    class Config:
        from_attributes = True  # Allows Pydantic to read data from SQLAlchemy/Supabase objects


# This will be use to verify which user is currently login by frontend
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
