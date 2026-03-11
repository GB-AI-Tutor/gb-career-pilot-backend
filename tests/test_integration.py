from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.main import app
from src.utils.security import create_access_token

client = TestClient(app)

FAKE_USER_ID = "fe4ad25e-b207-414a-8f4e-7d5a55daa3a6"
FAKE_USER_EMAIL = "2022n00020@gmail.com"

FAKE_USER = {
    "id": FAKE_USER_ID,
    "email": FAKE_USER_EMAIL,
    "full_name": "Test User",
}


def test_get_me_success():
    # 1. Generate a fresh token
    user_data = {"sub": FAKE_USER_ID, "email": FAKE_USER_EMAIL}
    expires = datetime.now(UTC) + timedelta(hours=1)
    token = create_access_token(user_data, expires)

    # 2. Mock the Supabase DB call so CI doesn't need real credentials
    mock_response = MagicMock()
    mock_response.data = FAKE_USER

    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_response

    with patch("src.api.v1.deps.get_supabase_client", return_value=mock_client):
        # 3. Hit the protected endpoint
        response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    # 4. Assert
    assert response.status_code == 200
    assert "email" in response.json()


def test_get_me_unauthorized():
    # Testing the integration when the token is missing
    response = client.get("/api/v1/users/me")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"
