from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from src.main import app
from src.utils.security import create_access_token

client = TestClient(app)

# The real user UUID that exists in the database
REAL_USER_ID = "fe4ad25e-b207-414a-8f4e-7d5a55daa3a6"
REAL_USER_EMAIL = "2022n00020@gmail.com"


def test_get_me_success():
    # 1. Generate a fresh token every time the test runs — never expires during the test
    user_data = {"sub": REAL_USER_ID, "email": REAL_USER_EMAIL}
    expires = datetime.now(UTC) + timedelta(hours=1)
    token = create_access_token(user_data, expires)

    # 2. We hit the protected endpoint with the 'Authorization' header
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    # 3. We check if it all integrated correctly
    assert response.status_code == 200
    assert "email" in response.json()


def test_get_me_unauthorized():
    # Testing the integration when the token is missing
    response = client.get("/api/v1/users/me")

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"
