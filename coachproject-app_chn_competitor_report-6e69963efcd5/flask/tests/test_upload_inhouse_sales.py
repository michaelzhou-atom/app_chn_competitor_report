import pytest
import json
from io import BytesIO
import pandas as pd
from app.models import InhouseSalesData

@pytest.mark.parametrize('role', ['admin'])
def test_upload_inhouse_sales_success(client, mocker):
    """Test for successful upload of in-house sales file."""
    # Mock the upsert_data method to avoid actual DB operations
    mock_upsert = mocker.patch('app.models.inhouse_sales_model.InhouseSalesData.upsert_data')

    # Create a dummy DataFrame with the correct structure
    df = pd.DataFrame({
        'year': [2025],
        'month': [8],
        'manager_name': ['Test Manager'],
        'store_code': ['TS01'],
        'store_name': ['Test Store'],
        'brand_name': ['Test Brand'],
        'amount': [1000.50],
        'comp': ['Y'],
        'comment': ['Test comment'],
        'store_category': ['Retail']
    })

    # Save the DataFrame to an in-memory Excel file
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')
    excel_file.seek(0)

    # Prepare the data for the POST request
    data = {
        'file': (excel_file, 'inhouse_sales.xlsx')
    }

    # Send the file in a POST request
    response = client.post('/backend/upload-inhouse-sales', data=data, content_type='multipart/form-data')

    # Assert the response
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['message'] == "Successfully upserted 1 records."

    # Assert that the mocked method was called once
    mock_upsert.assert_called_once()
