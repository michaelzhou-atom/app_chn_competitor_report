# tests/test_auth.py
import pytest
import json
from app.models import Auth
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash, check_password_hash


@pytest.mark.parametrize('role', ['admin'])
def test_login_success(client):
    """Test for successful login with correct credentials"""
    # Mocking Auth.get_creds method to return a valid user object
    with patch.object(Auth, 'get_creds') as mock_get_creds:
        # Create a mock object that simulates a real user object returned from the database
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.password = generate_password_hash("password123")
        mock_user.role = "admin"
        
        # Mocking the get_creds method to return the mock user object
        mock_get_creds.return_value = mock_user

        # Sending POST request to /login with valid data
        response = client.post(
            '/backend/auth/login',
            json={"username": "testuser", "password": "password123"}
        )

        # Asserting status code and presence of token in response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "token" in data
        assert data["role"] == "admin"

@pytest.mark.parametrize('role', ['admin'])
def test_login_failure(client):
    """Test for failed login attempt with incorrect credentials"""
    # Mocking Auth.get_creds method to simulate invalid credentials
    with patch.object(Auth, 'get_creds') as mock_get_creds:
        # Create a mock object for invalid credentials (e.g., no user found)
        mock_get_creds.return_value = None  # Simulating invalid credentials

        # Sending POST request with invalid credentials
        response = client.post(
            '/backend/auth/login',
            json={"username": "testuser", "password": "wrongpassword"}
        )

        # Asserting the response contains the correct failure message
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["message"] == "Unable to authenticate!"
