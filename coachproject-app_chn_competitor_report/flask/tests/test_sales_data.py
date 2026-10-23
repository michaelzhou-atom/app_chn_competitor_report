import pytest
import json
import pandas as pd
from unittest.mock import patch


@pytest.mark.parametrize("role", ["manager"])
def test_sales_data(client):
    """Test for sales data route."""
    with patch("app.controllers.main.load_list_data") as mock_load_list_data, patch(
        "app.models.SalesData.get_sales_data"
    ) as mock_get_sales_data:

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
                    "sales": 5185.0,
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
                    "sales": 4185.0,
                    "comp": "Y",
                    "comment": "老顾客邀约下降",
                    "store_category_db": "Retail",
                },
            ]
        )

        response = client.get("/backend/sales-data/CNOCF10")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "sales_data" in data["data"]
        assert len(data["data"]["sales_data"]) == 1

        sales_data = data["data"]["sales_data"]
        record = sales_data[0]
        assert record["sales"] - record["ly_sales"] == 1000.0


@pytest.mark.parametrize("role", ["manager"])
def test_sales_data_with_no_list_data(client):
    """Test for sales data route."""
    with patch("app.controllers.main.load_list_data") as mock_load_list_data, patch(
        "app.models.SalesData.get_sales_data"
    ) as mock_get_sales_data:

        # Mock load_list_data return value
        mock_load_list_data.return_value = {
            "list_df": pd.DataFrame([], columns=[
                    "store",
                    "store_name",
                    "manager",
                    "year",
                    "month",
                    "brand",
                    "store_category",
                    "status",
                    "manager_code",
                    "brand_code",
                ]),
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
                    "sales": 5185.0,
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
                    "sales": 4185.0,
                    "comp": "Y",
                    "comment": "老顾客邀约下降",
                    "store_category_db": "Retail",
                },
            ]
        )

        response = client.get("/backend/sales-data/CNOCF10")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "sales_data" in data["data"]
        assert len(data["data"]["sales_data"]) == 0

@pytest.mark.parametrize("role", ["manager"])
def test_sales_data_with_multiple_sales_record_ty(client):
    """Test for sales data route. If there are multiple last year's sales data record."""
    with patch("app.controllers.main.load_list_data") as mock_load_list_data, patch(
        "app.models.SalesData.get_sales_data"
    ) as mock_get_sales_data:

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
                    "sales": 5185.0,
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
                    "sales": 5184.0,
                    "comp": "Y",
                    "comment": "老顾客邀约下降",
                    "store_category_db": "Retail",
                },
                # {
                #     "year": 2023,
                #     "month": 9,
                #     "manager_db": "Vivian Wang",
                #     "store": "CNOCF10",
                #     "store_name_db": "Handan New Century",
                #     "brand": "Lancome",
                #     "sales": 4186.0,
                #     "comp": "Y",
                #     "comment": "老顾客邀约下降",
                #     "store_category_db": "Retail",
                # },
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
            ]
        )

        response = client.get("/backend/sales-data/CNOCF10")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "sales_data" in data["data"]
        assert len(data["data"]["sales_data"]) == 2

        sales_data = data["data"]["sales_data"]
        record = sales_data[0]
        assert record["sales"] - record["ly_sales"] == 1000.0
        
@pytest.mark.parametrize("role", ["manager"])
def test_sales_data_with_multiple_sales_record_ly(client):
    """Test for sales data route. If there are multiple last year's sales data record."""
    with patch("app.controllers.main.load_list_data") as mock_load_list_data, patch(
        "app.models.SalesData.get_sales_data"
    ) as mock_get_sales_data:

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
                    "sales": 5185.0,
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
                    "sales": 4185.0,
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
                    "sales": 4184.0,
                    "comp": "Y",
                    "comment": "老顾客邀约下降",
                    "store_category_db": "Retail",
                },
            ]
        )

        response = client.get("/backend/sales-data/CNOCF10")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "sales_data" in data["data"]
        assert len(data["data"]["sales_data"]) == 2

        sales_data = data["data"]["sales_data"]
        record = sales_data[0]
        assert record["sales"] - record["ly_sales"] == 1000.0
    
@pytest.mark.parametrize("role", ["manager"])
def test_sales_data_with_multiple_sales_record_duplicates(client):
    """Test for sales data route. If there are multiple duplicate sales data record."""
    with patch("app.controllers.main.load_list_data") as mock_load_list_data, patch(
        "app.models.SalesData.get_sales_data"
    ) as mock_get_sales_data:

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
                    "sales": 5185.0,
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
                    "sales": 5184.0,
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
                    "sales": 4186.0,
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
                    "sales": 4185.0,
                    "comp": "Y",
                    "comment": "老顾客邀约下降",
                    "store_category_db": "Retail",
                },
            ]
        )

        response = client.get("/backend/sales-data/CNOCF10")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "sales_data" in data["data"]
        assert len(data["data"]["sales_data"]) == 4
    

