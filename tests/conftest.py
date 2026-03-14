"""Test fixtures for API endpoint testing.

Fixtures are reusable test setup functions that pytest automatically injects into tests.
They reduce code duplication and manage setup/teardown.
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def student_data():
    """Sample student data for testing registration endpoint.

    This fixture provides valid test data that matches the UserRegister schema.
    It's used across multiple tests to ensure consistent test data.
    """
    return {
        "email": "student2@gmail.com",
        "full_name": "Ali Khan",
        "phone": "03489940593",
        "city": "Gilgit",
        "field_of_interest": "Engineering",
        "password_hash": "123asdas",
        "fsc_percentage": 85.0,
    }


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for unit tests.

    This fixture provides a mocked Supabase client that simulates database behavior
    without making real API calls. Used for fast, isolated unit tests.

    The mock has chainable methods to simulate Supabase query builder pattern:
    client.table("users").select("email").eq("email", value).execute()
    """
    mock_client = MagicMock()
    return mock_client


@pytest.fixture
def mock_supabase_client_no_existing_user(mock_supabase_client):
    """Mock Supabase that simulates NO existing user in database.

    This is used when testing successful registration (duplicate check should pass).
    """
    # When checking for existing email, return empty data (no user found)
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )
    return mock_supabase_client


@pytest.fixture
def mock_supabase_client_existing_user(mock_supabase_client, student_data):
    """Mock Supabase that simulates EXISTING user in database.

    This is used when testing duplicate email rejection (should return 409).
    """
    # When checking for existing email, return user data (user already exists)
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"email": student_data["email"]}]
    )
    return mock_supabase_client


@pytest.fixture
def mock_supabase_login_success(mock_supabase_client, student_data):
    from src.utils.security import get_password_hash

    hashed_password = get_password_hash(student_data["password_hash"])

    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "user-123",
                "email": student_data["email"],
                "full_name": student_data["full_name"],
                "password": hashed_password,
            }
        ]
    )

    return mock_supabase_client


@pytest.fixture
def mock_supabase_login_wrong_password(mock_supabase_client, student_data):
    from src.utils.security import get_password_hash

    hashed_password = get_password_hash("wrong password")

    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "user-123",
                "email": student_data["email"],
                "full_name": student_data["full_name"],
                "password": hashed_password,
            }
        ]
    )

    return mock_supabase_client


@pytest.fixture
def mock_supabase_login_user_not_found(mock_supabase_client, student_data):
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )
    return mock_supabase_client


@pytest.fixture
def mock_supabase_get_current_user(mock_supabase_client, student_data):
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "user_123", **student_data}]
    )
    return mock_supabase_client


@pytest.fixture
def mock_supabase_update_profile(student_data, mock_supabase_client):
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {
                "full_name": student_data["full_name"],
                "phone": student_data["phone"],
                "fsc_percentage": student_data["fsc_percentage"],
                "city": student_data["city"],
                "field_of_interest": student_data["field_of_interest"],
            }
        ]
    )
    return mock_supabase_client


# ============================================================================
# DEPENDENCY OVERRIDE FIXTURES - For testing endpoints with authentication
# ============================================================================


@pytest.fixture
def mock_current_user_data(student_data):
    """
    Mock authenticated user data returned by get_current_user dependency.

    This simulates what the dependency returns after successful authentication.
    Used to test endpoints that require @Depends(get_current_user).
    """
    return {
        "id": "user-123",
        "email": student_data["email"],
        "full_name": student_data["full_name"],
        "phone": student_data["phone"],
        "city": student_data["city"],
        "fsc_percentage": student_data["fsc_percentage"],
        "field_of_interest": student_data["field_of_interest"],
    }


@pytest.fixture
def authenticated_client(mock_current_user_data):
    """
    Override the get_current_user dependency for testing protected endpoints.

    This fixture:
    1. Replaces get_current_user with a mock that returns authenticated user data
    2. Allows you to test endpoints without real JWT tokens
    3. Cleans up after the test

    Usage:
        def test_protected_endpoint(authenticated_client):
            response = authenticated_client.get("/api/v1/users/me")
            assert response.status_code == 200
    """
    # Import here to avoid module resolution issues at test collection time
    from src.api.v1.deps import get_current_user
    from src.main import app

    # Create a function that returns the mock user data
    def override_get_current_user():
        return mock_current_user_data

    # Override the dependency
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield  # Test runs here with dependency overridden

    # Cleanup: Remove the override after test
    app.dependency_overrides.clear()
