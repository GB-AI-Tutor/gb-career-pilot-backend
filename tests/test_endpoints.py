from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_register_user_success():
    mock_supabase_client = MagicMock()

    # Simulate no existing user found (empty list = no duplicate)
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
    ])

    with patch("src.database.database.get_supabase_client", return_value=mock_supabase_client), \
            patch("src.api.v1.endpoints.auth.send_verification_email") as mock_email:

        payload = {
            "email": "test@student.com",
            "password_hash": "testpassword123",
            "full_name": "Test Student",
            "phone": "03001234567",
            "fsc_percentage": 85.5,
            "city": "Gilgit",
            "field_of_interest": "Computer Science",
        }
        response = client.post("/api/v1/users/Registeration", json=payload)

        assert response.status_code == 200
        assert response.json()[
            "Message"] == " Verification mail has been send."
        mock_email.assert_called_once()
