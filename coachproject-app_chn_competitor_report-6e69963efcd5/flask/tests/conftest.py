# tests/conftest.py

import pytest
import datetime
import jwt
from app import create_app

# Fixture to initialize the Flask app
@pytest.fixture
def app():
    # Create a Flask app instance with test configuration
    app = create_app()  # Factory function to create app
    app.config.from_object('config.TestConfig')  # Using TestConfig from config.py
    yield app  # This will be the app object available in tests

# Fixture to provide a test client
@pytest.fixture
def client(app, role):
    # Create a test client for the app
    client = app.test_client()

    # Generate token based on the role provided (admin or manager)
    token = generate_token(app, role)

    # Set the Authorization header to simulate an authenticated request
    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'

    return client
    
def generate_token(app, role):
    """
    Helper function to generate a JWT token based on the role.
    Generates a token for either 'admin' or 'manager'.
    """
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=app.config["JWT_EXP_DURATION"]
    )
    
    if role == 'admin':
        username = "admin"
    elif role == 'manager':
        username = "manager"
    else:
        raise ValueError("Invalid role specified. Must be 'admin' or 'manager'.")
    
    token = jwt.encode(
        {
            "user": username,
            "role": role,
            "exp": expiration_time
        },
        app.config["JWT_SECRET"],
        algorithm="HS256"
    )
    return token

