import os
import json
import pandas as pd
from flask import current_app
import boto3
import psycopg2
from ..models import ListData
from io import StringIO
from functools import wraps
from flask import request, jsonify, current_app
import jwt


# Decorator to require authentication using JWT
def role_should_be(required_role=None):
    def token_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            required_role_list = required_role.split(",")
            token = None

            # First, check if the token is passed in the request headers
            auth_header = request.headers.get("Authorization")
            if auth_header:
                header_val = auth_header.split(" ")
                if len(header_val) == 2:
                    token = header_val[1]

            # If no token in the Authorization header, check the query string
            if not token:
                token = request.args.get("token")

            if not token:
                return jsonify({"message": "Token is missing!"}), 403

            try:
                # Decode the token using the secret key
                data = jwt.decode(
                    token, current_app.config["JWT_SECRET"], algorithms=["HS256"]
                )
                current_user = data[
                    "user"
                ]  # You can extract user info from the token payload
                current_role = data["role"]

                if current_role not in required_role_list:
                    return jsonify({"message": "Do not have sufficient claims!"}), 401

            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Token has expired!"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"message": "Invalid token!"}), 401
            except Exception as e:
                return jsonify({"message": "Could not authorize the user!"}), 401

            return f(*args, **kwargs)

        return decorated_function

    return token_required


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # Check if the token is passed in the request headers
        key_name = current_app.config["API_KEY_NAME"]
        key_value = current_app.config["API_KEY_VALUE"]

        header_key_val = None
        if key_name in request.headers:
            header_key_val = request.headers[key_name]

        if not header_key_val:
            return jsonify({"message": "API KEY is missing!"}), 403

        if header_key_val != key_value:
            return jsonify({"message": "API key is invalid!"}), 401

        return f(*args, **kwargs)

    return decorated_function


# Function to fetch the secret from AWS Secrets Manager
def get_airflow_secret(secret_name="AIRFLOW/keyrotation_service_account", secret_region='ap-southeast-1'):
    # Set up Boto3 Secrets Manager client
    secrets_client = boto3.client("secretsmanager", region_name=secret_region)

    # Fetch the secret value from AWS Secrets Manager
    response = secrets_client.get_secret_value(SecretId=secret_name)

    # Parse the secret JSON string
    secret = json.loads(response["SecretString"])
    return secret["username"], secret["password"]


# Function to fetch the secret from AWS Secrets Manager
def get_db_secret(secret_name="COMPETITORAPP/POSTGRES_DEV", secret_region='ap-southeast-1'):
    # Set up Boto3 Secrets Manager client
    secrets_client = boto3.client("secretsmanager", region_name=secret_region)

    # Fetch the secret value from AWS Secrets Manager
    response = secrets_client.get_secret_value(SecretId=secret_name)

    # Parse the secret JSON string
    secret = json.loads(response["SecretString"])
    return secret["username"], secret["password"]

def get_rds_db_secret(secret_name="redshift-copy-credentials", secret_region='ap-southeast-1'):
    # Set up Boto3 Secrets Manager client
    secrets_client = boto3.client("secretsmanager", region_name=secret_region)

    # Fetch the secret value from AWS Secrets Manager
    response = secrets_client.get_secret_value(SecretId=secret_name)

    # Parse the secret JSON string
    secret = json.loads(response["SecretString"])
    return secret["username"], secret["password"], secret["host"], secret["port"], secret["dbname"]


def get_db_conn():
    secret_name = os.getenv("AWS_DATABASE_SECRET", "COMPETITORAPP/POSTGRES_DEV")

    # Fetch DB credentials from Secrets Manager
    username, password = get_db_secret(secret_name)

    # PostgreSQL connection parameters
    host = "tpr-datafabric-cn-airflowdb-dev-ap-southeast-1.csld0v7ouojj.ap-southeast-1.rds.amazonaws.com"
    port = 5361
    dbname = "competitor_app"

    # Establish connection to PostgreSQL
    conn = psycopg2.connect(
        dbname=dbname, user=username, password=password, host=host, port=port
    )

    return conn


def convert_df_to_csv(df):
    from io import BytesIO
    csv_output = BytesIO()
    df.to_csv(csv_output, index=False, encoding='utf-8')
    csv_output.seek(0)  # Rewind the BytesIO object to the beginning
    return csv_output


# Function to check allowed file extensions
def allowed_file(filename):
    try:
        current_app.logger.debug(f"[ALLOWED_FILE] Checking file: {filename}")
        
        if "." not in filename:
            current_app.logger.warning(f"[ALLOWED_FILE] No extension found in filename: {filename}")
            return False
            
        extension = filename.rsplit(".", 1)[1].lower()
        allowed_extensions = current_app.config.get("ALLOWED_EXTENSIONS", [])
        
        current_app.logger.debug(f"[ALLOWED_FILE] File extension: {extension}")
        current_app.logger.debug(f"[ALLOWED_FILE] Allowed extensions: {allowed_extensions}")
        
        is_allowed = extension in allowed_extensions
        current_app.logger.info(f"[ALLOWED_FILE] File '{filename}' validation result: {is_allowed}")
        
        return is_allowed
        
    except Exception as e:
        current_app.logger.error(f"[ALLOWED_FILE] Error validating filename '{filename}': {e}")
        return False


def validate_columns(df, expected_columns):
    try:
        current_app.logger.info(f"[VALIDATE_COLUMNS] Starting column validation")
        current_app.logger.debug(f"[VALIDATE_COLUMNS] DataFrame shape: {df.shape}")
        current_app.logger.debug(f"[VALIDATE_COLUMNS] Original DataFrame columns: {list(df.columns)}")
        
        # Handle both list and dict formats for expected_columns
        if isinstance(expected_columns, list):
            current_app.logger.debug(f"[VALIDATE_COLUMNS] Expected columns (list format): {expected_columns}")
            # Convert list to dict with None type (skip type validation)
            expected_columns_dict = {col: None for col in expected_columns}
            validate_types = False
        elif isinstance(expected_columns, dict):
            current_app.logger.debug(f"[VALIDATE_COLUMNS] Expected columns (dict format): {list(expected_columns.keys())}")
            expected_columns_dict = expected_columns
            validate_types = True
        else:
            raise ValueError(f"expected_columns must be a list or dict, got {type(expected_columns)}")
        
        # Normalize column names to lowercase for comparison
        df_columns_lower = {col.lower().strip(): col for col in df.columns}
        expected_columns_lower = {col.lower().strip(): expected_type for col, expected_type in expected_columns_dict.items()}
        
        current_app.logger.debug(f"[VALIDATE_COLUMNS] Normalized DataFrame columns: {list(df_columns_lower.keys())}")
        current_app.logger.debug(f"[VALIDATE_COLUMNS] Normalized expected columns: {list(expected_columns_lower.keys())}")
        
        errors = []

        # Check if the DataFrame contains the expected columns (case-insensitive)
        missing_columns = set(expected_columns_lower.keys()) - set(df_columns_lower.keys())
        if missing_columns:
            error_msg = f"Missing columns: {', '.join(missing_columns)}"
            current_app.logger.warning(f"[VALIDATE_COLUMNS] {error_msg}")
            errors.append(error_msg)

        # Handle extra columns based on input format
        extra_columns = set(df_columns_lower.keys()) - set(expected_columns_lower.keys())
        if extra_columns:
            if validate_types:  # Dict format - preserve existing behavior (treat as error)
                error_msg = f"Extra columns: {', '.join(extra_columns)}"
                current_app.logger.info(f"[VALIDATE_COLUMNS] {error_msg}")
                errors.append(error_msg)
            else:  # List format - be more lenient (just log as info)
                current_app.logger.info(f"[VALIDATE_COLUMNS] Extra columns found (ignoring): {', '.join(extra_columns)}")

        # Check if the column types are correct (only for dict format)
        if validate_types:
            for expected_col_lower, expected_type in expected_columns_lower.items():
                if expected_col_lower in df_columns_lower:
                    original_col_name = df_columns_lower[expected_col_lower]
                    actual_type = df[original_col_name].dtype
                    current_app.logger.debug(f"[VALIDATE_COLUMNS] Column '{original_col_name}' (normalized: '{expected_col_lower}'): actual={actual_type}, expected={expected_type}")
                    if actual_type != expected_type:
                        error_msg = f"Column '{original_col_name}' has type {actual_type}, expected {expected_type}"
                        current_app.logger.warning(f"[VALIDATE_COLUMNS] {error_msg}")
                        errors.append(error_msg)
        else:
            current_app.logger.debug(f"[VALIDATE_COLUMNS] Skipping type validation (list format used)")

        if errors:
            current_app.logger.error(f"[VALIDATE_COLUMNS] Validation failed with {len(errors)} errors: {errors}")
        else:
            current_app.logger.info(f"[VALIDATE_COLUMNS] Validation passed successfully")

        return errors if errors else None
        
    except Exception as e:
        current_app.logger.error(f"[VALIDATE_COLUMNS] Exception during validation: {e}")
        current_app.logger.error(f"[VALIDATE_COLUMNS] expected_columns type: {type(expected_columns)}, value: {expected_columns}")
        current_app.logger.error(f"[VALIDATE_COLUMNS] DataFrame columns: {list(df.columns)}", exc_info=True)
        return [f"Validation error: {str(e)}"]


def load_list_data():

    cache = current_app.cache
    cached_data = cache.get("cached_data")

    if cached_data == None:

        list_df = ListData.fetch_all_data()

        managers_list_df = (
            list_df.groupby("manager_code")
            .agg(
                manager=(
                    "manager",
                    "first",
                ),  # Get the first manager for each manager_code
                store_count=("store", "nunique"),  # Count distinct stores
            )
            .reset_index()
        )

        the_year = 0
        the_month = 0
        if list_df.shape[0] > 0:
            the_year = list_df["year"].to_list()[0]
            the_month = list_df["month"].to_list()[0]

        dict_list = {
            "list_df": list_df,
            "the_year": the_year,
            "the_month": the_month,
            "managers_df": managers_list_df,
        }

        cache.set("cached_data", dict_list)
        cached_data = dict_list

    return cached_data


def rotate_df(merged_data, the_year):

    # divide data into two years
    ty_database = merged_data[(merged_data["year"] == the_year)]
    ly_database = merged_data[(merged_data["year"] == the_year - 1)]

    # rename sales to ly_sales for ly data
    ly_database.rename(columns={"sales": "ly_sales"}, inplace=True)

    # exclude comment because only ty comments would be displayed and updated
    ly_database = ly_database[
        ["year", "month", "manager", "store", "store_name", "brand", "ly_sales"]
    ]

    ly_database["year"] = ly_database["year"] + 1
    # merge ly sales into ty data for display
    combined_sales = ty_database.merge(
        ly_database,
        on=["year", "month", "manager", "store", "store_name", "brand"],
        how="inner",
    )

    return combined_sales


def extend_df(list_df, the_year, store_code):
    list_ly = list_df.copy(deep=True)
    list_ly["year"] = int(the_year) - 1
    df = pd.concat([list_df, list_ly])
    df = df[df["store"] == store_code]
    return df


def split_df(updated_sales, ly_db_sales_data):
    # Divide the comming data into tow parts and prepare last year data frame separately
    ly_update_sales = updated_sales.copy(deep=True)
    ly_update_sales["sales"] = ly_update_sales["ly_sales"]
    ly_update_sales["year"] = ly_update_sales["year"] - 1
    # combine last year sales data with new data to preserve
    ly_update_sales = ly_update_sales[
        [
            "year",
            "month",
            "manager",
            "store",
            "store_name",
            "brand",
            "sales",
            "store_category",
        ]
    ]
    ly_db_sales_data = ly_db_sales_data[["store", "brand", "year", "month", "comp", "comment"]]
    ly_update_sales = ly_update_sales.merge(
        ly_db_sales_data, on=["store", "brand", "year", "month"], how="left"
    )

    col_list = [
        "year",
        "month",
        "manager",
        "store",
        "store_name",
        "brand",
        "sales",
        "comp",
        "comment",
        "store_category",
    ]
    updated_sales = updated_sales[col_list]

    ly_update_sales = ly_update_sales[col_list]

    # Combine the data and process some data types
    df_form_final = pd.concat([updated_sales, ly_update_sales]).reset_index(drop=True)
    df_form_final["year"] = df_form_final["year"].astype("int")
    df_form_final["month"] = df_form_final["month"].astype("int")
    df_form_final.loc[df_form_final["sales"] == "", "sales"] = 0
    df_form_final["sales"] = df_form_final["sales"].astype("double")

    return df_form_final

def check_comp(row, df):
    composite_key_cols = ["store_code", "month", "brand_name", "store_category"]
    prev_year = row["year"] - 1
    mask = (df["year"] == prev_year)
    for col in composite_key_cols:
        mask &= (df[col] == row[col])
    
    # Check if previous year record exists and get its amount
    prev_year_records = df[mask]
    if prev_year_records.shape[0] > 0:
        prev_year_amount = prev_year_records.iloc[0]["amount"]
        # Both current year and last year amounts must be > 0
        return "Y" if row["amount"] > 0 and prev_year_amount > 0 else "N"
    return "N"
