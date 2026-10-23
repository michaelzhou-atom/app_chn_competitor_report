import pytest
import json
import pandas as pd
from unittest.mock import patch


@pytest.mark.parametrize("role", ["manager"])
def test_update_data(client):
    """Test for updating sales data."""
    with patch("app.models.SalesData.get_sales_data") as mock_get_sales_data, patch(
        "app.models.SalesData.delete_and_insert"
    ) as mock_delete_and_insert:

        # Mock SalesData methods
        mock_get_sales_data.return_value = pd.DataFrame(
            [
                {
                    "year": 2023,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 4185.0,
                    "comp": "Y",
                    "comment": "老顾客邀约下降",
                    "store_category_db": "Retail",
                },
                {
                    "year": 2024,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 5185.0,
                    "comp": "Y",
                    "comment": "老顾客邀约下降",
                    "store_category_db": "Retail",
                },
            ]
        )
        mock_delete_and_insert.return_value = None

        # Prepare sample data for request
        request_data = {
            "sales_data": [
                {
                    "brand": "Lancome",
                    "brand_code": "lancome",
                    "comment": "updated comment",
                    "comp": "N",
                    "growth_rate": 0,
                    "ly_sales": 100,
                    "manager": "Vivian Wang",
                    "month": 9,
                    "sales": 200,
                    "status": "Open",
                    "store": "CNOCF10",
                    "store_category": "Retail",
                    "store_name": "Handan New Century",
                    "year": 2024,
                }
            ],
            "year": 2024,
            "month": 9,
            "store_code": "CNOCF10",
        }

        response = client.post("/backend/update-data", json=request_data)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data

        updated_data = data["data"]
        this_year_record = updated_data[0]
        last_year_record = updated_data[1]

        assert this_year_record["year"] == 2024 and last_year_record["year"] == 2023
        assert this_year_record["amount"] == 200 and last_year_record["amount"] == 100
        assert this_year_record["comment"] == "updated comment"



@pytest.mark.parametrize("role", ["manager"])
def test_update_data_update_record(client):
    """Test for updating sales data when there is existing sales record. This will update the data"""
    with patch("app.models.SalesData.get_sales_data") as mock_get_sales_data, patch(
        "app.models.SalesData.delete_and_insert"
    ) as mock_delete_and_insert, patch(
        "app.controllers.main.load_list_data"
    ) as mock_load_list_data:

        # Mock SalesData methods
        mock_get_sales_data.return_value = pd.DataFrame(
             [
                {
                    "year": 2024,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 200.0,
                    "comp": "Y",
                    "comment": "老顾客邀约下降",
                    "store_category_db": "Retail",
                },
                {
                    "year": 2023,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 100.0,
                    "comp": None,
                    "comment": None,
                    "store_category_db": "Retail",
                },
            ]
        )
        mock_delete_and_insert.return_value = None

        # Prepare sample data for request
        request_data = {
            "sales_data": [
                {
                    "brand": "Lancome",
                    "brand_code": "lancome",
                    "comment": "updated comment",
                    "comp": "N",
                    "growth_rate": 0,
                    "ly_sales": 100,
                    "manager": "Vivian Wang",
                    "month": 9,
                    "sales": 200,
                    "status": "Open",
                    "store": "CNOCF10",
                    "store_category": "Retail",
                    "store_name": "Handan New Century",
                    "year": 2024,
                }
            ],
            "year": 2024,
            "month": 9,
            "store_code": "CNOCF10",
        }

        response = client.post("/backend/update-data", json=request_data)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data

        # Mock load_list_data return value
        mock_load_list_data.return_value = {
            "list_df": pd.DataFrame(
                [
                    {
                        "store": "CNOCF10",
                        "store_name": "CN Guangzhou Panyu FA Str",
                        "manager": "Vivian Wang",
                        "year": 2024,
                        "month": 9,
                        "brand": "Lancome",
                        "store_category": "Retail",
                        "status": "Open",
                        "manager_code": "vivian_wang",
                        "brand_code": "lancome",
                    }
                ]
            ),
            "the_year": 2024,
            "the_month": 9,
        }

        # Mock sales data response
        mock_get_sales_data.return_value = pd.DataFrame(
            [
                {
                    "year": 2024,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 200.0,
                    "comp": "Y",
                    "comment": "updated comment",
                    "store_category_db": "Retail",
                },
                {
                    "year": 2023,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 100.0,
                    "comp": None,
                    "comment": None,
                    "store_category_db": "Retail",
                },
            ]
        )

        response = client.get("/backend/sales-data/CNOCF10")
        data = json.loads(response.data)
        updated_data = data["data"]["sales_data"]
        updated_data = updated_data[0]

        assert updated_data["year"] == 2024
        assert updated_data['sales'] == 200 and updated_data['ly_sales'] == 100
        assert updated_data["comment"] == "updated comment"

@pytest.mark.parametrize("role", ["manager"])
def test_update_data_insert_record(client):
    """Test for updating sales data when there is no existing sales record. This will insert the data"""
    with patch("app.models.SalesData.get_sales_data") as mock_get_sales_data, patch(
        "app.models.SalesData.delete_and_insert"
    ) as mock_delete_and_insert, patch(
        "app.controllers.main.load_list_data"
    ) as mock_load_list_data:

        # Mock SalesData methods
        mock_get_sales_data.return_value = pd.DataFrame(
            [
                {
                    "year": 2024,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 200.0,
                    "comp": "Y",
                    "comment": "updated comment",
                    "store_category_db": "Retail",
                },
                {
                    "year": 2023,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 100.0,
                    "comp": None,
                    "comment": None,
                    "store_category_db": "Retail",
                },
            ]
        )
        mock_delete_and_insert.return_value = None

        # Prepare sample data for request
        request_data = {
            "sales_data": [
                {
                    "brand": "Nike",
                    "brand_code": "nike",
                    "comment": "老顾客邀约下降",
                    "comp": "N",
                    "growth_rate": 0,
                    "ly_sales": 300,
                    "manager": "Quingwen",
                    "month": 9,
                    "sales": 400,
                    "status": "Open",
                    "store": "CNOCF10",
                    "store_category": "Outlet",
                    "store_name": "Handan New Century",
                    "year": 2024,
                }
            ],
            "year": 2024,
            "month": 9,
            "store_code": "CNOCF10",
        }

        response = client.post("/backend/update-data", json=request_data)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "data" in data

        # Mock load_list_data return value
        mock_load_list_data.return_value = {
            "list_df": pd.DataFrame(
                [
                    {
                        "store": "CNOCF10",
                        "store_name": "CN Guangzhou Panyu FA Str",
                        "manager": "Quingwen",
                        "year": 2024,
                        "month": 9,
                        "brand": "Nike",
                        "store_category": "Retail",
                        "status": "Open",
                        "manager_code": "quingwen",
                        "brand_code": "nike",
                    }
                ]
            ),
            "the_year": 2024,
            "the_month": 9,
        }

        # Mock sales data response
        mock_get_sales_data.return_value = pd.DataFrame(
            [
                {
                    "year": 2024,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 200.0,
                    "comp": "Y",
                    "comment": "updated comment",
                    "store_category_db": "Retail",
                },
                {
                    "year": 2023,
                    "month": 9,
                    "manager_db": "Vivian Wang",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Lancome",
                    "sales": 100.0,
                    "comp": None,
                    "comment": None,
                    "store_category_db": "Retail",
                },
                {
                    "year": 2024,
                    "month": 9,
                    "manager_db": "Quingwen",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Nike",
                    "sales": 400.0,
                    "comp": "Y",
                    "comment": "updated comment",
                    "store_category_db": "Retail",
                },
                {
                    "year": 2023,
                    "month": 9,
                    "manager_db": "Quingwen",
                    "store": "CNOCF10",
                    "store_name_db": "Handan New Century",
                    "brand": "Nike",
                    "sales": 300.0,
                    "comp": None,
                    "comment": None,
                    "store_category_db": "Retail",
                },
            ]
        )

        response = client.get("/backend/sales-data/CNOCF10")
        data = json.loads(response.data)
        updated_data = data["data"]["sales_data"]
        updated_data = updated_data[0]
        

        assert updated_data["year"] == 2024
        assert updated_data['sales'] == 400 and updated_data['ly_sales'] == 300


