import pytest
import json
import pandas as pd
from unittest.mock import patch

@pytest.mark.parametrize('role', ['manager'])
def test_stores_list(client):
    """Test for stores list route."""
    with patch("app.controllers.main.load_list_data") as mock_load_list_data:
        mock_load_list_data.return_value = {
            "list_df": pd.DataFrame([
                {"store": "S01", "manager_code": "M01", "store_name": "Store 1", "status": "Active"},
                {"store": "S02", "manager_code": "M01", "store_name": "Store 2", "status": "Active"}
            ])
        }

        response = client.get('/backend/stores-list/M01')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["data"]["stores_list"]) == 2
        assert data["data"]["stores_list"][0]["store"] == "S01"
