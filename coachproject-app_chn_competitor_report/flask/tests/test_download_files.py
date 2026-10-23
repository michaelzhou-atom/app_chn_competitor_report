import pytest
from unittest.mock import patch, MagicMock, ANY  # Import mock.ANY from unittest.mock
from io import BytesIO
import pandas as pd

@pytest.mark.parametrize('role', ['admin'])
def test_download_data(client):
    """Test for downloading data."""

    # Sample mocked DataFrames for outlet and retail data
    outlet_data = pd.DataFrame({
        'store': ['S01'],
        'store_name': ['Store 1'],
        'sales': [1000],
        'year': [2023],
        'month': [1]
    })

    retail_data = pd.DataFrame({
        'store': ['S01'],
        'store_name': ['Store 1'],
        'sales': [1500],
        'year': [2023],
        'month': [1]
    })

    # Mock the SalesData.get_reports_data method to return the mocked DataFrames
    with patch('app.models.SalesData.get_reports_data') as mock_get_reports_data:
        mock_get_reports_data.side_effect = [outlet_data, retail_data]

        # Mock convert_df_to_csv to return a BytesIO object containing CSV content
        with patch('app.helpers.convert_df_to_csv') as mock_convert_df_to_csv:
            mock_convert_df_to_csv.side_effect = lambda df: BytesIO(df.to_csv(index=False).encode())

            # Mock the zip file creation and sending of the file via send_file
            with patch('zipfile.ZipFile') as mock_zipfile:
                mock_zip = MagicMock()
                mock_zipfile.return_value = mock_zip
                mock_zip.writestr = MagicMock()

                # Add debugging output
                print("Starting the client.get request...")

                # Send the GET request to the /backend/download-data endpoint with query params
                response = client.get('/backend/download-data?start_year=2020&end_year=2023&month=1')

                # Debugging: Ensure that the code inside download_data() is executed
                print(f"Response status code: {response.status_code}")
                print(f"Response content type: {response.content_type}")

                # Check if writestr was called
                print(f"Mock ZipFile calls: {mock_zip.writestr.call_args_list}")

                # Assertions to validate the response
                assert response.status_code == 200
                assert response.content_type == 'application/zip'
