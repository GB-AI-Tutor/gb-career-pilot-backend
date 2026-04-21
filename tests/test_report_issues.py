from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_create_report_issue_success(authenticated_client):
    mock_db = MagicMock()
    mock_query = MagicMock()

    mock_db.table.return_value = mock_query
    mock_query.insert.return_value = mock_query
    mock_query.execute = AsyncMock(
        return_value=MagicMock(
            data=[
                {
                    "id": 1,
                    "status": "open",
                    "created_at": "2026-04-21T10:00:00+00:00",
                }
            ]
        )
    )

    payload = {
        "category": "Bug",
        "subject": "Search page throws 500",
        "description": "Submitting search with filters results in server error",
        "page_url": "/universities/programs/search",
        "contact_email": "qa@example.com",
    }

    with patch(
        "src.api.v1.endpoints.report_issues.get_supabase_admin_client",
        new=AsyncMock(return_value=mock_db),
    ):
        response = client.post("/api/v1/report-issues", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["message"] == "Issue created"
    assert body["status"] == "open"
    assert body["created_at"] == "2026-04-21T10:00:00+00:00"
