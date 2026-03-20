from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, computed_field

# --- Enums for strict validation ---


class SectorEnum(str, Enum):
    PUBLIC = "Public"
    PRIVATE = "Private"
    SEMI_GOVERNMENT = "Semi-Government"


# --- Program Schemas ---


class ProgramBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Software Engineering"])
    duration_years: int = Field(..., ge=1, le=5)
    estimated_total_fee: float = Field(..., ge=0)
    has_specific_scholarships: bool = False


class ProgramCreate(ProgramBase):
    university_id: UUID
    # We don't include description_embedding here as it's usually
    # handled by the ML service before saving to DB.


class ProgramResponse(ProgramBase):
    model_config = ConfigDict(
        from_attributes=True
    )  # Allows Pydantic to read SQLAlchemy/Supabase objects

    id: UUID
    university_id: UUID
    created_at: datetime


# --- University Schemas ---


class UniversityBase(BaseModel):
    id: int | None = Field(None, exclude=True)
    name: Annotated[str, StringConstraints(to_lower=True)] = Field(
        ..., min_length=3, max_length=200
    )
    city: Annotated[str, StringConstraints(to_lower=True)] = Field(..., min_length=2, max_length=50)
    sector: SectorEnum
    website: HttpUrl | None = None
    ranking_national: int | None = None
    qs_ranking_: int | None = None
    founded_year: int | None = None
    fee_per_semester: int | None = None
    is_active: bool | None = None
    has_hostel: bool = False
    has_general_scholarships: bool = False

    @property
    @computed_field
    def uni_id(self) -> str:
        if self.id is not None:
            # Formats 1 -> "uni_001", 12 -> "uni_012"
            return f"uni_{self.id:03}"
        return "uni_pending"


class UniversityCreate(UniversityBase):
    pass


class UniversityResponse(UniversityBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    # We can nest programs if we want to return them with the university
    programs: list[ProgramResponse] = []


class UniversityUpdate(BaseModel):
    name: Annotated[str, StringConstraints(to_lower=True)] | None = Field(
        default=None, min_length=3, max_length=200
    )
    city: str | None = Field(default=None, min_length=2, max_length=50)
    sector: SectorEnum | None = Field(default=None)
    website: HttpUrl | None = None
    has_hostel: bool = False
    has_general_scholarships: bool = False
    # programs : list[ProgramBase] | None = Field(default=None)


class UniversitySearchArgs(BaseModel):
    location: str | None = Field(
        None, description=" The city or region to search in (e.g, 'Lahore', 'Gilgit')"
    )
    program_name: str | None = Field(
        None, description="The Subject or Degree field(e.g., 'Computer Science' ,'Nursing)"
    )

    max_fee: int | None = Field(
        None, description=" The Maximum annual tuition fee the student can afford."
    )


# --- Admission Requirements ---


class AdmissionRequirementBase(BaseModel):
    min_fsc_percentage: float = Field(..., ge=0, le=100)
    required_entry_test: str = Field(..., min_length=2)


class AdmissionResponse(AdmissionRequirementBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    program_id: UUID
