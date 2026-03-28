# API endpoint tests with proper unit and integration test patterns.
# Unit Tests: Mock the database, test endpoint logic in isolation

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


# ============================================================================
# UNIT TESTS - Database is mocked, tests run fast and isolated
# ============================================================================
def test_register_new_email_success_unit(student_data, mock_supabase_client_no_existing_user):
    """
    Unit test: Endpoint accepts new email.

    This is a UNIT TEST because:
    - Database is MOCKED (no real Supabase calls)
    - Tests that duplicate check passes for new emails
    - Endpoint should return 200 and send verification email
    """
    with patch(
        "src.database.database.get_supabase_client",
        return_value=mock_supabase_client_no_existing_user,
    ), patch("src.api.v1.endpoints.users.send_verification_email") as mock_email:
        response = client.post("/api/v1/users/Registeration", json=student_data)

        # Should succeed when email doesn't exist
        assert response.status_code == 200
        assert "Verification mail" in response.json()["Message"]

        # Email should have been sent
        mock_email.assert_called_once()
        assert mock_email.call_args[0][0] == student_data["email"]


def test_register_duplicate_email_unit(student_data, mock_supabase_client_existing_user):
    """
    Unit test: Endpoint rejects duplicate email.

    This is a UNIT TEST because:
    - Database is MOCKED (no real Supabase calls)
    - No actual data is persisted
    - Test runs in milliseconds
    - Tests endpoint logic only1

    What it tests:
    - When user tries to register with an email that exists in DB,
      endpoint returns 409 Conflict
    """
    # Patch the database client with our mock
    with patch(
        "src.database.database.get_supabase_client",
        return_value=mock_supabase_client_existing_user,
    ), patch("src.api.v1.endpoints.users.send_verification_email") as mock_email:
        # Try to register with duplicate email
        response = client.post("/api/v1/users/Registeration", json=student_data)

        # Assert correct status code
        assert response.status_code == 409, "Should reject duplicate email"

        # Assert correct error message
        response_json = response.json()
        assert "already registered" in response_json["detail"].lower()

        # Email should NOT have been sent
        mock_email.assert_not_called()


def test_login_success_unit_test(student_data, mock_supabase_login_success):
    # login unit test will be successful if the email and password match with the database and it should return access token and refresh token
    login_payload = {"email": student_data["email"], "password": student_data["password_hash"]}

    with patch(
        "src.database.database.get_supabase_admin_client", return_value=mock_supabase_login_success
    ):
        response = client.post("/api/v1/auth/login", json=login_payload)

        assert response.status_code == 200
        response_json = response.json()
        assert "access_token" in response_json
        assert "refresh_token" in response_json
        assert response_json["Token_type"] == "bearer"


def test_login_wrong_password(student_data, mock_supabase_login_wrong_password):
    # This test sends correct email but wrong password
    login_payload = {
        "email": student_data["email"],
        # Different from student_data['password_hash']
        "password": "WrongPassword123",
    }

    with patch(
        "src.database.database.get_supabase_admin_client",
        return_value=mock_supabase_login_wrong_password,
    ):
        response = client.post("/api/v1/auth/login", json=login_payload)

        assert response.status_code == 401, "Invalid Credentials"


def test_login_noneexistent_user(student_data, mock_supabase_client_no_existing_user):
    # This test uses a non-existent email
    login_payload = {
        "email": "nonexistent@gmail.com",  # Email that doesn't exist
        "password": student_data["password_hash"],
    }

    with patch(
        "src.database.database.get_supabase_admin_client",
        return_value=mock_supabase_client_no_existing_user,
    ):
        response = client.post("/api/v1/auth/login", json=login_payload)
        if response.status_code == 404:
            print("validation error:", response.json())
        assert response.status_code == 404


def test_get_current_user(authenticated_client, student_data):
    """
    Unit test: Get current user information.

    Uses authenticated_client fixture which overrides get_current_user dependency.
    This simulates an authenticated user without needing a real JWT token.
    """
    # authenticated_client fixture handles dependency override
    response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["email"] == student_data["email"]
    assert response_json["full_name"] == student_data["full_name"]


def test_update_profile(authenticated_client, student_data, mock_supabase_client_no_existing_user):
    """
    Unit test: Update user profile.

    Uses authenticated_client fixture which overrides get_current_user dependency.
    Also mocks the database to avoid real API calls during update.
    """
    update_data = {
        "full_name": "Updated Name",
        "phone": "03001234567",
        "fsc_percentage": 90.0,
        "city": "Islamabad",
        "field_of_interest": "Computer Science",
    }

    # authenticated_client handles get_current_user override
    # We also need to mock the database update call
    with patch(
        "src.database.database.get_supabase_client",
        return_value=mock_supabase_client_no_existing_user,
    ):
        response = client.put("/api/v1/users/update_user_info", json=update_data)

        assert response.status_code == 200
        response_json = response.json()
        assert "Data Updated Successfully" in response_json["Detail"]
