from fastapi import APIRouter, Depends, HTTPException, status

from src.api.v1.deps import get_current_user
from src.database.database import get_supabase_admin_client
from src.schemas.report_issues import ReportIssueCreate, ReportIssueCreateResponse

router = APIRouter()


@router.post("/report-issues", response_model=ReportIssueCreateResponse)
async def create_report_issue(
    payload: ReportIssueCreate,
    current_user: dict = Depends(get_current_user),
):
    client = await get_supabase_admin_client()

    try:
        response = (
            await client.table("report_issues")
            .insert(
                {
                    "user_id": current_user["id"],
                    "category": payload.category.value,
                    "subject": payload.subject,
                    "description": payload.description,
                    "page_url": payload.page_url,
                    "contact_email": payload.contact_email,
                }
            )
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create issue",
            )

        issue = response.data[0]
        return {
            "id": issue["id"],
            "message": "Issue created",
            "status": issue.get("status", "open"),
            "created_at": issue["created_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create issue: {str(e)}",
        ) from e
