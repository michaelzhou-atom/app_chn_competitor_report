import pytest
import json
from unittest.mock import patch


@pytest.mark.parametrize('role', ['admin'])
def test_toggle_edit_settings(client):
    """Test for toggling last year data editable setting."""
    with patch("app.models.AppSetting.toggle_last_year_data_editable") as mock_toggle_last_year_data_editable:
        # Mock the toggle behavior
        mock_toggle_last_year_data_editable.return_value = True

        response = client.post('/backend/toggle-edit-settings')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["data"]["is_last_year_data_editable"] is True
