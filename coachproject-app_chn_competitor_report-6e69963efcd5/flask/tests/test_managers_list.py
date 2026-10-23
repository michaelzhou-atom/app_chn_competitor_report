import pytest
import json
import pandas as pd
from unittest.mock import patch

@pytest.mark.parametrize('role', ['manager'])
def test_managers_list(client):
    """Test for managers list route."""
    with patch("app.controllers.main.load_list_data") as mock_load_list_data:
        # Mocking the return value for load_list_data
        mock_load_list_data.return_value = {
            "managers_df": pd.DataFrame([{"manager_code": "M01", "manager_name": "John"}])
        }

        response = client.get('/backend/managers-list')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["data"]["managers_list"]) == 1
        assert data["data"]["managers_list"][0]["manager_code"] == "M01"
