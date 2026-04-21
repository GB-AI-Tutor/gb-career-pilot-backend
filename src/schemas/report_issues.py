from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class IssueCategory(str, Enum):
    bug = "Bug"
    data_error = "Data Error"
    recommendation_issue = "Recommendation Issue"
    ui_ux = "UI/UX"
    performance = "Performance"
    other = "Other"


class ReportIssueCreate(BaseModel):
    category: IssueCategory
    subject: str
    description: str
    page_url: str
    contact_email: EmailStr | None = Field(default=None)


class ReportIssueCreateResponse(BaseModel):
    id: int
    message: str
    status: str
    created_at: str
