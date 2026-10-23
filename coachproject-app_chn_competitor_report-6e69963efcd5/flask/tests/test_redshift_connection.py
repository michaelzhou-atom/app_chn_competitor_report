import pytest
from sqlalchemy import text
from app.models import db

def test_redshift_connection(app):
    """
    Tests the connection to the Redshift database by executing a simple query.
    This test requires the environment to be configured with the necessary AWS
    credentials and environment variables for the Redshift connection.
    """
    with app.app_context():
        try:
            # Get the engine for the 'redshift' bind
            engine = db.get_engine('redshift')
            with engine.connect() as connection:
                # Execute a simple query
                result = connection.execute(text("SELECT 1")).scalar()
                # Assert that the result is 1
                assert result == 1
        except Exception as e:
            pytest.fail(f"Redshift connection test failed with an exception: {e}")
