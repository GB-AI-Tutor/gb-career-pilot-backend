from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_get_me_success():
    # 1. First, we need a real token. We can simulate a login or
    # manually create a token using our utility.
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2RhdGEiOnsic3ViIjoiZmU0YWQyNWUtYjIwNy00MTRhLThmNGUtN2Q1YTU1ZGFhM2E2IiwiZW1haWwiOiIyMDIybjAwMDIwQGdtYWlsLmNvbSJ9LCJleHAiOjE3NzMyOTA1MjZ9.n2L6mXL56eAuAh8vAVDcW7vjK0d_78uxI7dcGhmmrNc"

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
