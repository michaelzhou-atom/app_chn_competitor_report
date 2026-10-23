import pytest
import json
from io import BytesIO
import pandas as pd

@pytest.mark.parametrize('role', ['admin'])
def test_upload_list(client):
    """Test for uploading list file."""
    df = pd.DataFrame({
        "store": ["CNOC169"],
        "store_name": ["Shanghai Bailian Youyicheng"],
        "manager": ["objectDonnie Zhang"],
        "year": [2024],
        "month": [9],
        "brand": ["Balenciaga"],
        "store_category": ["Retail"],
        "status": ["Open"]
    })

    # Save the DataFrame to an in-memory Excel file
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, sheet_name="data", engine='openpyxl')

    # Seek to the beginning of the file before sending
    excel_file.seek(0)

    # Prepare the data to be sent in the POST request
    data = {
        'file': (excel_file, 'list.xlsx')  # Attach the file with the correct filename
    }

    # Send the file in a POST request to the /upload-list endpoint
    response = client.post('/backend/upload-list', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "data" in data

@pytest.mark.parametrize('role', ['admin'])
def test_upload_list_failed(client):
    """Test for uploading list file incorrect file uploaded."""
    # The store col is missing in the sheet
    df = pd.DataFrame({
        "store_name": ["Shanghai Bailian Youyicheng"],
        "manager": ["objectDonnie Zhang"],
        "year": [2024],
        "month": [9],
        "brand": ["Balenciaga"],
        "store_category": ["Retail"],
        "status": ["Open"]
    })

    # Save the DataFrame to an in-memory Excel file
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, sheet_name="data", engine='openpyxl')

    # Seek to the beginning of the file before sending
    excel_file.seek(0)

    # Prepare the data to be sent in the POST request
    data = {
        'file': (excel_file, 'list.xlsx')  # Attach the file with the correct filename
    }

    # Send the file in a POST request to the /upload-list endpoint
    response = client.post('/backend/upload-list', data=data, content_type='multipart/form-data')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "data" in data
