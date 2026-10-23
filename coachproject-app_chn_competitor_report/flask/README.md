# Flask API Documentation

This documentation provides details on the available API endpoints, how to interact with them using a tool like Postman, and what to expect in return.

**Base URL**: `http://127.0.0.1:8000/backend`

**Global Headers**:
Some endpoints require an API key for access. This is provided via the `Api-Key` header.

| Header | Value | Description |
| --- | --- | --- |
| `Api-Key` | `your_api_key_here` | The API key for authenticating requests to protected endpoints. |

---

## Authentication Endpoints (`/auth`)

These endpoints handle user authentication, registration, and password management.

### 1. User Login

*   **Endpoint:** `POST /auth/login`
*   **Description:** Authenticates a user based on their username and password and returns a JWT token for session management.
*   **Postman Setup:**
    *   **Method:** `POST`
    *   **URL:** `http://127.0.0.1:8000/backend/auth/login`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Content-Type` | `application/json` |
    *   **Body (raw, JSON):**
        ```json
        {
            "username": "some_user",
            "password": "user_password"
        }
        ```
*   **Success Response (200 OK):**
    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "role": "manager"
    }
    ```
*   **Error Response (401 Unauthorized):**
    ```json
    {
        "message": "Unable to authenticate!"
    }
    ```

### 2. Register New User

*   **Endpoint:** `POST /auth/register`
*   **Description:** Creates a new user with a specified username, password, and role. Requires a valid API key.
*   **Postman Setup:**
    *   **Method:** `POST`
    *   **URL:** `http://127.0.0.1:8000/backend/auth/register`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Content-Type` | `application/json` |
        | `Api-Key` | `your_api_key_here` |
    *   **Body (raw, JSON):**
        ```json
        {
            "username": "new_user",
            "password": "new_password",
            "role": "manager"
        }
        ```
*   **Success Response (200 OK):**
    ```json
    {
        "data": []
    }
    ```
*   **Error Response (500 Internal Server Error):**
    ```json
    {
        "message": "could not create user",
        "error": "..."
    }
    ```

### 3. Change User Password

*   **Endpoint:** `POST /auth/change-password`
*   **Description:** Updates the password for an existing user. Requires a valid API key.
*   **Postman Setup:**
    *   **Method:** `POST`
    *   **URL:** `http://127.0.0.1:8000/backend/auth/change-password`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Content-Type` | `application/json` |
        | `Api-Key` | `your_api_key_here` |
    *   **Body (raw, JSON):**
        ```json
        {
            "username": "existing_user",
            "password": "a_very_new_password",
            "role": "manager"
        }
        ```
*   **Success Response (200 OK):**
    ```json
    {
        "data": []
    }
    ```
*   **Error Response (500 Internal Server Error):**
    ```json
    {
        "message": "could not update password",
        "error": "..."
    }
    ```

---

## Main Application Endpoints (`/`)

These endpoints handle the core application logic, including data retrieval, updates, and administrative tasks. A valid JWT token is required for most of these endpoints.

**Authorization Header for Main Endpoints:**

| Header | Value | Description |
| --- | --- | --- |
| `Authorization` | `Bearer <your_jwt_token>` | The JWT token obtained from the `/login` endpoint. |

### 1. Get Managers List

*   **Endpoint:** `GET /managers-list`
*   **Description:** Retrieves a list of all managers. Requires `manager` or `admin` role.
*   **Postman Setup:**
    *   **Method:** `GET`
    *   **URL:** `http://127.0.0.1:8000/backend/managers-list`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Authorization` | `Bearer <your_jwt_token>` |
*   **Success Response (200 OK):**
    ```json
    {
        "data": {
            "managers_list": [
                {
                    "manager_code": "manager_1",
                    "manager": "Manager One"
                }
            ]
        }
    }
    ```

### 2. Get Stores List for a Manager

*   **Endpoint:** `GET /stores-list/<manager_code>`
*   **Description:** Retrieves a list of stores associated with a specific manager code. Requires `manager` role.
*   **Postman Setup:**
    *   **Method:** `GET`
    *   **URL:** `http://127.0.0.1:8000/backend/stores-list/manager_1`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Authorization` | `Bearer <your_jwt_token>` |
*   **Success Response (200 OK):**
    ```json
    {
        "data": {
            "stores_list": [
                {
                    "store": "S001",
                    "store_name": "Store One",
                    "status": "Active"
                }
            ]
        }
    }
    ```

### 3. Get Sales Data for a Store

*   **Endpoint:** `GET /sales-data/<store_code>`
*   **Description:** Retrieves detailed sales data for a specific store, comparing current year sales with the previous year. Requires `manager` role.
*   **Postman Setup:**
    *   **Method:** `GET`
    *   **URL:** `http://127.0.0.1:8000/backend/sales-data/S001`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Authorization` | `Bearer <your_jwt_token>` |
*   **Success Response (200 OK):**
    ```json
    {
        "data": {
            "sales_data": [
                {
                    "year": 2025,
                    "month": 8,
                    "manager": "Manager One",
                    "store": "S001",
                    "store_name": "Store One",
                    "status": "Active",
                    "brand": "Nike",
                    "sales": 15000,
                    "ly_sales": 12000,
                    "comp": "Y",
                    "growth_rate": 25.0,
                    "comment": "Good performance"
                }
            ],
            "year": 2025,
            "month": 8,
            "store_code": "S001",
            "is_last_year_data_editable": false
        }
    }
    ```

### 4. Update Sales Data

*   **Endpoint:** `POST /update-data`
*   **Description:** Updates the sales figures and comments for a given store, month, and year. Requires `manager` role.
*   **Postman Setup:**
    *   **Method:** `POST`
    *   **URL:** `http://127.0.0.1:8000/backend/update-data`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Content-Type` | `application/json` |
        | `Authorization` | `Bearer <your_jwt_token>` |
    *   **Body (raw, JSON):**
        ```json
        {
            "sales_data": [
                {
                    "brand": "Nike",
                    "sales": 16000,
                    "ly_sales": 12000,
                    "comment": "Updated comment"
                }
            ],
            "year": 2025,
            "month": 8,
            "store_code": "S001"
        }
        ```
*   **Success Response (200 OK):**
    ```json
    {
        "data": [
            {
                "year": 2025,
                "month": 8,
                "store_code": "S001",
                "brand_name": "Nike",
                "amount": 16000,
                "comment": "Updated comment"
            }
        ]
    }
    ```

### 5. Upload Master List

*   **Endpoint:** `POST /upload-list`
*   **Description:** Uploads an Excel file (`.xlsx`, `.xls`) containing the master list of stores, brands, and managers. Requires `admin` role.
*   **Postman Setup:**
    *   **Method:** `POST`
    *   **URL:** `http://127.0.0.1:8000/backend/upload-list`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Authorization` | `Bearer <your_jwt_token>` |
    *   **Body (form-data):**
        | Key | Value |
        | --- | --- |
        | `file` | (Select your `.xlsx` or `.xls` file) |
*   **Success Response (200 OK):**
    ```json
    {
        "data": [
            {
                "store": "S001",
                "store_name": "Store One",
                "manager": "Manager One",
                "year": 2025,
                "month": 8,
                "brand": "Nike",
                "store_category": "Retail",
                "status": "Active"
            }
        ]
    }
    ```
*   **Error Response (400 Bad Request):**
    ```json
    {
        "error": "File type not allowed",
        "messages": []
    }
    ```

### 6. Download Sales Data Report

*   **Endpoint:** `GET /download-data`
*   **Description:** Downloads a ZIP file containing two CSVs (`outlet_data.csv`, `retail_data.csv`) for a specified date range. Requires `admin` role.
*   **Postman Setup:**
    *   **Method:** `GET`
    *   **URL:** `http://127.0.0.1:8000/backend/download-data`
    *   **Params:**
        | Key | Value |
        | --- | --- |
        | `start_year` | `2024` |
        | `end_year` | `2025` |
        | `month` | `8` |
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Authorization` | `Bearer <your_jwt_token>` |
*   **Success Response:** A `data_files.zip` file will be downloaded.

### 7. Get System Logs

*   **Endpoint:** `GET /logs`
*   **Description:** Retrieves system logs within a specified date range. Requires `admin` role.
*   **Postman Setup:**
    *   **Method:** `GET`
    *   **URL:** `http://127.0.0.1:8000/backend/logs`
    *   **Params:**
        | Key | Value |
        | --- | --- |
        | `from` | `2025-08-01` |
        | `to` | `2025-08-28` |
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Authorization` | `Bearer <your_jwt_token>` |
*   **Success Response (200 OK):**
    ```json
    [
        {
            "log_id": 1,
            "timestamp": "2025-08-28T10:00:00",
            "user": "some_user",
            "action": "UPDATE_SALES",
            "details": "..."
        }
    ]
    ```

### 8. Trigger ETL Pipeline

*   **Endpoint:** `POST /etl-pipeline`
*   **Description:** Starts the Airflow ETL pipeline. Requires `admin` role.
*   **Postman Setup:**
    *   **Method:** `POST`
    *   **URL:** `http://127.0.0.1:8000/backend/etl-pipeline`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Authorization` | `Bearer <your_jwt_token>` |
*   **Success Response (200 OK):**
    ```json
    {
        "message": "Pipeline started successfully",
        "response": { ... }
    }
    ```
*   **Error Response (500 Internal Server Error):**
    ```json
    {
        "error": "Failed to start pipeline",
        "status_code": 500,
        "response": "..."
    }
    ```

### 9. Settings Endpoints (Admin)

*   **Description:** These endpoints manage application settings. Require `admin` role.
*   **Endpoints:**
    *   `GET /get-edit-settings`: Retrieves the current value of the `is_last_year_data_editable` setting.
    *   `POST /toggle-edit-settings`: Toggles the boolean value of the `is_last_year_data_editable` setting.
*   **Postman Setup:**
    *   **Method:** `GET` or `POST`
    *   **URL:** `http://127.0.0.1:8000/backend/get-edit-settings` or `http://127.0.0.1:8000/backend/toggle-edit-settings`
    *   **Headers:**
        | Key | Value |
        | --- | --- |
        | `Authorization` | `Bearer <your_jwt_token>` |
*   **Response for `GET` and `POST`:**
    ```json
    {
        "data": {
            "is_last_year_data_editable": true
        }
    }
    ```