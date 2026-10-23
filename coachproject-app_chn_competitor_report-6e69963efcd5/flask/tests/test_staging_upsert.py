import pytest
import json
import os
from app.models import InhouseSalesData

@pytest.mark.parametrize('role', ['admin'])
def test_staging_upsert_endpoint(client, mocker):
    """Tests the endpoint that uses the staging table upsert method."""
    # Mock the target function to prevent actual DB operations
    mock_upsert = mocker.patch('app.models.inhouse_sales_model.InhouseSalesData.upsert_with_staging')

    # Define the path to the test file
    # Note: This assumes the test is run from the 'flask' directory root
    file_path = os.path.join('app', 'static', 'uploads', 'house_brand_data_source_monthly.xlsx')

    try:
        with open(file_path, 'rb') as f:
            data = {
                'file': (f, 'house_brand_data_source_monthly.xlsx')
            }

            # IMPORTANT: Replace with the actual endpoint you created
            endpoint_url = '/test-staging-upsert' 

            response = client.post(endpoint_url, data=data, content_type='multipart/form-data')

    except FileNotFoundError:
        pytest.fail(f"Test file not found at: {file_path}. Make sure the path is correct.")

    # Assert the response
    assert response.status_code == 200
    
    # Assert that the mocked method was called once
    mock_upsert.assert_called_once()
