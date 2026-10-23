import os
import pandas as pd
import numpy as np
from flask import Blueprint, jsonify, request, current_app, send_file
import threading
import concurrent.futures
from ..helpers import (
    load_list_data,
    rotate_df,
    extend_df,
    split_df,
    allowed_file,
    convert_df_to_csv,
    role_should_be,
    validate_columns,
    check_comp,
)
from ..helpers.etl_helpers import get_airflow_config, start_pipeline_workflow, check_pipeline_status_workflow
from ..models import (
    ListData,
    SalesData,
    LogData,
    AppSetting,
    StoreStatus,
    InhouseSalesData,
    CompetitorSalesStatistics,
    cohpure_clr_sku_list,
    db,
)

main = Blueprint("main", __name__, url_prefix="/backend")


@main.route("/")
def index():

    df = ListData.fetch_all_data()
    data = df.to_dict(orient="records")
    return jsonify({"data": len(data)}), 200


@main.route("/managers-list")
@role_should_be("manager,admin")
def managers_list():

    dict_list = load_list_data()
    managers_df = dict_list["managers_df"]

    managers_list = managers_df.to_dict(orient="records")

    return jsonify({"data": {"managers_list": managers_list}})


@main.route("/stores-list/<manager_code>")
@role_should_be("manager")
def stores_list(manager_code):

    # load cached data - helper
    # filter with manager code
    # parse and return results

    dict_list = load_list_data()
    list_df = dict_list["list_df"]

    stores = list_df[list_df["manager_code"] == manager_code][
        ["store", "store_name", "status"]
    ].sort_values(by="status", ascending=False)
    stores_list = stores.drop_duplicates().to_dict(orient="records")

    return jsonify({"data": {"stores_list": stores_list}})


@main.route("/sales-data/<store_code>")
@role_should_be("manager")
def sales_data(store_code):

    # load list data from cache - helper
    # fetch sales data
    # merge list data and sales data
    # rotate df - helper
    # add comp col
    # calculate growth rate
    # parse and return response

    dict_list = load_list_data()
    list_df = dict_list["list_df"]
    the_year = dict_list["the_year"]
    the_month = dict_list["the_month"]

    store_data = extend_df(list_df, the_year, store_code)

    with current_app.app_context():
        sales_data = SalesData.get_sales_data(the_year - 1, the_month, store_code)
        sales_data.columns = [
            "year",
            "month",
            "manager_db",  # manager_name renamed to prevent conflict
            "store",  # store_code renamed to match store data
            "store_name_db",  # store_name renamed to prevent conflict
            "brand",  # brand_name renamed to match store data
            "sales",
            "comp",
            "comment",
            "store_category_db",  # store_category renamed to prevent conflict
        ]

    # merge list data with sales data so that every brand from list data appear in response
    merged_data = store_data.merge(
        sales_data, on=["year", "month", "store", "brand"], how="left"
    )
    merged_data = merged_data[
        [
            "year",
            "month",
            "manager",
            "store",
            "store_name",
            "status",
            "brand",
            "sales",
            "comp",
            "comment",
            "store_category",
            "brand_code",
        ]
    ]

    # rotate df to get this year sales and last year sales in same col
    combined_sales = rotate_df(merged_data, the_year)

    # add comp column
    # when ty_sales is null or ly_sales is null, comp = 'N', else comp = 'Y'
    combined_sales.fillna(0, inplace=True)
    combined_sales["comp"] = combined_sales.apply(
        lambda x: "Y" if x["sales"] > 0 and x["ly_sales"] > 0 else "N", axis=1
    )
    combined_sales.sort_values(by=["ly_sales", "sales"], ascending=False, inplace=True)
    

    # calculate growth rate
    # Apply the logic as described
    combined_sales["growth_rate"] = np.where(
        (combined_sales["ly_sales"].notna()) & (combined_sales["ly_sales"] != 0),
        # If ly_sales is not NaN, null, or 0, calculate the growth rate
        (
            (combined_sales["sales"] - combined_sales["ly_sales"])
            / combined_sales["ly_sales"]
        )
        * 100,
        np.where(
            (combined_sales["sales"].notna()) & (combined_sales["sales"] != 0),
            # If ly_sales is NaN, null, or 0, but sales is valid, growth rate = sales
            combined_sales["sales"],
            # If both ly_sales and sales are NaN, null, or 0, growth rate = 0
            0,
        ),
    )
    
    

    # reformat to list of dict and send the data to data collection page
    combined_sales = combined_sales.where(pd.notna(combined_sales), None)
    records = combined_sales.to_dict(orient="records")

    # get editable data settings from db
    is_last_year_data_editable = AppSetting.is_last_year_data_editable()

    return jsonify(
        {
            "data": {
                "sales_data": records,
                "year": the_year,
                "month": the_month,
                "store_code": store_code,
                "is_last_year_data_editable": is_last_year_data_editable,
            }
        }
    )


@main.route("/update-data", methods=["POST"])
@role_should_be("manager")
def update_data():

    # fetch settings from db
    # check if the toggle is allowed (No need to implement yet as FE is expected to prevent this)
    # get data from request and prepare
    # split data - helper
    # fetch last year sales data
    # prepare last year data
    # concat data
    # delete from db
    # dump in db
    # log this data
    # return response

    # Get and parse request params
    request_body = request.json
    sales_data = request_body["sales_data"]
    the_year = request_body["year"]
    the_month = request_body["month"]
    store_code = request_body["store_code"]

    # Create a dataframe from input data
    updated_sales = pd.DataFrame(sales_data)

    with current_app.app_context():
        ly_db_sales_data = SalesData.get_sales_data(the_year - 1, the_month, store_code)
        ly_db_sales_data.columns = [
            "year",
            "month",
            "manager_db",
            "store",
            "store_name_db",
            "brand",
            "sales",
            "comp",
            "comment",
            "store_category_db",
        ]

    # current year sales and last year sales is in one col
    # split this data and concat so it has only one sales col
    df_form_final = split_df(updated_sales, ly_db_sales_data)

    df_form_final.rename(
        columns={
            "sales": "amount",
            "store": "store_code",
            "brand": "brand_name",
            "manager": "manager_name",
        },
        inplace=True,
    )

    df_form_final = df_form_final.where(pd.notna(df_form_final), None)

    # Comp logic
    df_form_final["comp"] = df_form_final.apply(lambda x: check_comp(x, df_form_final), axis=1)

    #     # Add comp logic
    # df_form_final["comp"] = df_form_final.apply(
    #     lambda x: "Y" if x["amount"] > 0 and x["year"] - 1 == x["year"] else "N", axis=1
    # )

    with current_app.app_context():
        SalesData.delete_and_insert(df_form_final, the_year-1, the_month, store_code)
        LogData.bulk_insert(df_form_final)

    return_data = df_form_final.head()
    return_data = return_data.to_dict(orient="records")

    return jsonify({"data": return_data})


@main.route("/toggle-edit-settings", methods=["POST"])
@role_should_be("admin")
def toggle_edit_settings():
    new_value = AppSetting.toggle_last_year_data_editable()
    return jsonify({"data": {"is_last_year_data_editable": new_value}})


@main.route("/get-edit-settings")
@role_should_be("admin")
def get_edit_settings():
    is_last_year_data_editable = AppSetting.is_last_year_data_editable()
    return jsonify({"data": {"is_last_year_data_editable": is_last_year_data_editable}})


@main.route("/upload-list", methods=["POST"])
@role_should_be("admin")
def upload_list():
    # get list file from request body
    # save this file in uploads directory
    # load this file in pandas dataframe
    # parse and prepare content
    # update database

    if "file" not in request.files:
        return jsonify({"error": "No file part", 'messages': []}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file", 'messages': []}), 400

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed", 'messages': []}), 400

    # Save the file to the upload folder with sanitized filename
    filename = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(file.filename))
    file.save(filename)

    combination_counts = 0

    # Process the file with pandas
    try:

        expected_cols = {
            "store": "object",
            "store_name": "object",
            "manager": "object",
            "year": "int",
            "month": "int",
            "brand": "object",
            "store_category": "object",
            "status": "object",
        }

        list_df = pd.read_excel(filename, sheet_name="data")

        cols_errors = validate_columns(list_df, expected_cols)
        if cols_errors:
            return jsonify({"error": "Invalid file", 'messages': cols_errors}), 400

        # calculate manager code and brand code
        code_converter = lambda x: x.lower().strip().replace(" ", "_")
        list_df["manager_code"] = list_df["manager"].map(code_converter)
        list_df["brand_code"] = list_df["brand"].map(code_converter)
        list_df = list_df.where(pd.notna(list_df), None)

        combination_counts = (
            list_df
            .groupby(['store', 'year', 'month', 'brand', 'store_category'])
            .size()
            .reset_index(name='count')
            .query('count > 1')
        )

        with current_app.app_context():

            ListData.delete_and_insert(list_df)
            
            store_status_df = list_df[['store', 'year', 'month', 'brand', 'store_name', 'manager', 'store_category', 'status']]
            store_status_df.columns = ['store_code', 'year', 'month', 'brand_name', 'store_name', 'manager_name', 'store_category', 'status']
            StoreStatus.upsert_data(store_status_df)
            

        cache = current_app.cache
        cache.delete("cached_data")

        data = list_df.head().to_dict(orient="records")
        return jsonify({"data": data}), 200
    except Exception as e:
        current_app.logger.error(f"Error processing list file: {e}")
        error_messages = []
        if "UNIQUE constraint" in str(e) and len(combination_counts) > 0:
            error_messages.append({'error': 'UNIQUE constraint violations', 'data': combination_counts.to_dict(orient='records')})
            
        print(error_messages)
        return jsonify({"error": f"Error reading Excel file: {str(e)}", 'messages': error_messages}), 500


@main.route("/get-year-and-month")
def get_year_and_month():
    dict_list = load_list_data()
    year, month = dict_list.get('the_year', 0), dict_list.get('the_month', 0)
    
    year_and_month = ListData.year_and_month()
    
    # return jsonify({'data': {'year': year, 'month': month, 'year_and_month': year_and_month}})
    return jsonify({'data': year_and_month[0]})


@main.route("/upload-sku-list", methods=["POST"])
def upload_sku_list():
    """
    Added one more excel file(clearance_sku_list.xlsx with three fields style_color_code/effective_date/end_date) upload botton on the admin page, which would overwrite the redshift table prd_ind360.landing.cohpure_clr_sku_list
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file", 'messages': []}), 400

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed", 'messages': []}), 400

    # Save the file to the upload folder with sanitized filename
    filename = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(file.filename))
    file.save(filename)

    # Process the uploaded file
    try:
        df = pd.read_excel(filename)

        expected_columns = ["store_code", "cal_date", "clr_pce_ss_ttl_amt_lcl"]
        cols_errors = validate_columns(df, expected_columns)
        if cols_errors:
            return jsonify({"error": "Invalid file - missing or incorrect columns", 'messages': cols_errors}), 400

        thread = threading.Thread(target=cohpure_clr_sku_list.overwrite_in_background, args=(current_app._get_current_object(), df))
        thread.start()

        return jsonify({"message": "File upload received. Processing will continue in the background."}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


@main.route("/download-data")
@role_should_be("admin")
def download_data():
    # query data from database
    # parse data
    # return response

    start_year = request.args.get("start_year", type=int)
    end_year = request.args.get("end_year", type=int)
    month = request.args.get("month", type=int)

    current_app.logger.info(f"[DOWNLOAD_DATA] Request received - start_year={start_year}, end_year={end_year}, month={month}")

    if not start_year or not end_year or not month:
        current_app.logger.warning(f"[DOWNLOAD_DATA] Missing params - start_year={start_year}, end_year={end_year}, month={month}")
        return jsonify(
            {
                "message": "params missing",
                "rquired_params": ["start_year", "end_year", "month"],
            }
        ), 400

    try:
        current_app.logger.info(f"[DOWNLOAD_DATA] Fetching Outlet data...")
        outlet_data = SalesData.get_reports_data(start_year, end_year, month, "Outlet")
        current_app.logger.info(f"[DOWNLOAD_DATA] Outlet data shape: {outlet_data.shape if outlet_data is not None else 'None'}")
        
        current_app.logger.info(f"[DOWNLOAD_DATA] Fetching Retail data...")
        retail_data = SalesData.get_reports_data(start_year, end_year, month, "Retail")
        current_app.logger.info(f"[DOWNLOAD_DATA] Retail data shape: {retail_data.shape if retail_data is not None else 'None'}")
        
        # Check if data is empty
        outlet_empty = outlet_data is None or outlet_data.empty
        retail_empty = retail_data is None or retail_data.empty
        
        if outlet_empty and retail_empty:
            current_app.logger.warning(f"[DOWNLOAD_DATA] Both Outlet and Retail data are empty for params: start_year={start_year}, end_year={end_year}, month={month}")
            return jsonify({
                "error": "No data found",
                "message": f"No data available for the specified period (start_year={start_year}, end_year={end_year}, month={month})"
            }), 404
        
        if outlet_empty:
            current_app.logger.warning(f"[DOWNLOAD_DATA] Outlet data is empty")
        if retail_empty:
            current_app.logger.warning(f"[DOWNLOAD_DATA] Retail data is empty")

        # Convert the DataFrames to CSV format in memory
        current_app.logger.info(f"[DOWNLOAD_DATA] Converting DataFrames to CSV...")
        outlet_csv = convert_df_to_csv(outlet_data)
        retail_csv = convert_df_to_csv(retail_data)
        
        current_app.logger.info(f"[DOWNLOAD_DATA] Outlet CSV size: {len(outlet_csv.getvalue()) if outlet_csv else 0} bytes")
        current_app.logger.info(f"[DOWNLOAD_DATA] Retail CSV size: {len(retail_csv.getvalue()) if retail_csv else 0} bytes")

        # Send the two CSV files as a zip
        from zipfile import ZipFile
        from io import BytesIO

        # Create an in-memory zip file
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w") as zip_file:
            zip_file.writestr("outlet_data.csv", outlet_csv.getvalue())
            zip_file.writestr("retail_data.csv", retail_csv.getvalue())

        zip_buffer.seek(0)  # Rewind to the beginning
        zip_size = len(zip_buffer.getvalue())
        zip_buffer.seek(0)  # Rewind again after getting size
        
        current_app.logger.info(f"[DOWNLOAD_DATA] ZIP file created successfully, size: {zip_size} bytes")

        # Send the zip file as the response
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="data_files.zip",
            mimetype="application/zip",
        )

    except Exception as e:
        current_app.logger.error(f"[DOWNLOAD_DATA] Error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": "File Download Failed", "message": str(e)}), 500


@main.route("/etl-pipeline", methods=["POST"])
@role_should_be("admin")
def start_etl_pipeline():
    """Start ETL pipeline via Airflow API."""
    try:
        config = get_airflow_config()
        return start_pipeline_workflow(config)
    except Exception as e:
        current_app.logger.error(f"ETL pipeline error: {e}")
        return jsonify({"error": "Failed to start pipeline", "message": str(e)}), 500

@main.route('/check_status', methods=['POST'])
@role_should_be("admin")
def check_status():
    """Check the status of an Airflow DAG run."""
    return check_pipeline_status_workflow()

@main.route("/logs")
@role_should_be("admin")
def get_logs():

    date_from = request.args.get("from")
    date_to = request.args.get("to")

    # Validate query parameters
    if not date_from or not date_to:
        return jsonify({"error": "from and to params are required"}), 400

    log_data = LogData.get_all_data(date_from, date_to)
    data = log_data.to_dict(orient="records")

    return jsonify(data)

@main.route("/upload-inhouse-sales", methods=["POST"])
@role_should_be("admin")
def upload_inhouse_sales():
    current_app.logger.info("In-house sales upload endpoint called.")
    if "file" not in request.files:
        current_app.logger.warning("File part not found in request.")
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        current_app.logger.warning("No file selected.")
        return jsonify({"error": "No selected file"}), 400

    if not file or not allowed_file(file.filename):
        current_app.logger.warning(f"File type not allowed: {file.filename}")
        return jsonify({"error": "File type not allowed"}), 400

    filename = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(file.filename))
    file.save(filename)
    current_app.logger.info(f"File saved to {filename}")

    # Read Excel robustly: handle missing 'data' sheet, empty sheet, or invalid file
    current_app.logger.debug("[UPLOAD_INHOUSE] Starting processing for file=%s saved_path=%s", file.filename, filename)
    # 1. Open workbook (isolated)
    try:
        current_app.logger.debug("[UPLOAD_INHOUSE] Opening workbook")
        xl = pd.ExcelFile(filename)
        current_app.logger.debug("[UPLOAD_INHOUSE] Workbook sheets detected: %s", xl.sheet_names)
    except Exception as e:
        current_app.logger.warning(f"Invalid or corrupted Excel file: {e}")
        return jsonify({
            "error": "Failed to process file",
            "message": "File is not a valid Excel workbook or is corrupted."
        }), 400

    # 2. Validate expected sheet
    if "data" not in xl.sheet_names:
        current_app.logger.debug("[UPLOAD_INHOUSE] Missing required 'data' sheet. Sheets present: %s", xl.sheet_names)
        return jsonify({
            "error": "Failed to process file",
            "message": "Required sheet 'data' not found."
        }), 400

    # 3. Parse sheet
    try:
        current_app.logger.debug("[UPLOAD_INHOUSE] Parsing 'data' sheet")
        df = xl.parse("data")
        current_app.logger.debug("[UPLOAD_INHOUSE] DataFrame shape=%s columns=%s", df.shape, list(df.columns))
    except ValueError:
        return jsonify({
            "error": "Failed to process file",
            "message": "Unable to read 'data' sheet."
        }), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error reading 'data' sheet: {e}")
        return jsonify({
            "error": "Failed to process file",
            "message": "Unexpected error reading 'data' sheet."
        }), 400

    # 4. Basic data presence validation
    if df.shape[0] == 0 or df.dropna(how='all').empty:
        current_app.logger.debug("[UPLOAD_INHOUSE] Data sheet empty after NaN filtering")
        return jsonify({
            "error": "Failed to process file",
            "message": "Sheet 'data' has no data rows."
        }), 400
    # 5. Hybrid schema validation (attempt live Redshift, fallback to model) - isolated
    from sqlalchemy import text as _sql_text
    try:
        schema_name = InhouseSalesData.__table_args__.get('schema', 'public') if isinstance(InhouseSalesData.__table_args__, dict) else 'public'

        def _fetch_live_columns():
            # Prefer the exact redshift engine if available
            engine = None
            try:
                engine = db.engines.get('redshift')
            except Exception:
                engine = None
            if engine is None:
                try:
                    engine = db.get_engine(bind='redshift')
                except Exception:
                    engine = db.get_engine()  # fallback default bind

            table = InhouseSalesData.__tablename__
            cols: list[str] = []
            with engine.connect() as con:
                # Try SVV_COLUMNS (Redshift system view)
                q_svv = _sql_text(
                    """
                    SELECT column_name
                    FROM SVV_COLUMNS
                    WHERE table_schema = :schema
                      AND table_name = :table
                    ORDER BY ordinal_position
                    """
                )
                rows = con.execute(q_svv, {"schema": schema_name, "table": table}).fetchall()
                cols = [r[0] for r in rows]
                if cols:
                    return cols

                # Fallback to information_schema.columns
                q_info = _sql_text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = :schema
                      AND table_name = :table
                    ORDER BY ordinal_position
                    """
                )
                rows = con.execute(q_info, {"schema": schema_name, "table": table}).fetchall()
                cols = [r[0] for r in rows]
                if cols:
                    return cols

                # Final fallback: PG_TABLE_DEF
                q_pg = _sql_text(
                    """
                    SELECT "column" AS column_name
                    FROM PG_TABLE_DEF
                    WHERE schemaname = :schema
                      AND tablename = :table
                    ORDER BY ordinal_position
                    """
                )
                rows = con.execute(q_pg, {"schema": schema_name, "table": table}).fetchall()
                cols = [r[0] for r in rows]
            return cols

        try:
            current_app.logger.debug("[UPLOAD_INHOUSE] Attempting live schema fetch")
            live_cols = _fetch_live_columns()
            current_app.logger.info(f"[UPLOAD_INHOUSE] Live Redshift columns: {live_cols}")
        except Exception as live_err:
            current_app.logger.warning(f"[UPLOAD_INHOUSE] Live schema fetch failed, using model metadata: {live_err}")
            live_cols = []

        model_cols = [c.name for c in InhouseSalesData.__table__.columns]
        effective_cols = live_cols if live_cols else model_cols

        if live_cols and set(live_cols) != set(model_cols):
            current_app.logger.warning(f"[UPLOAD_INHOUSE] Schema drift detected. Model={model_cols} Redshift={live_cols}")

        required_core = ["year", "month", "store_code", "brand_name", "amount"]
        required_cols = required_core

        normalized_file_map = {c.lower().strip(): c for c in df.columns}
        missing = [col for col in required_cols if col.lower() not in normalized_file_map]
        if missing:
            current_app.logger.warning(f"[UPLOAD_INHOUSE] Missing required columns: {missing}; file columns: {list(df.columns)}")
            # Ensure all items in missing are strings to prevent join() errors
            missing_str = [str(col) for col in missing]
            current_app.logger.info("[UPLOAD_INHOUSE] About to return 400 error for missing columns")
            raise ValueError(f"Missing required column(s): {', '.join(missing_str)}")

        extras = [orig for norm, orig in normalized_file_map.items() if norm not in {c.lower() for c in effective_cols}]
        if extras:
            current_app.logger.info(f"[UPLOAD_INHOUSE] Ignoring extra columns: {extras}")
        current_app.logger.info("[UPLOAD_INHOUSE] Schema validation passed (hybrid). Effective cols used: %s", effective_cols)
    except ValueError as ve:
        current_app.logger.info(f"[UPLOAD_INHOUSE] Validation failed: {ve}")
        return jsonify({
            "error": "Failed to process file",
            "message": str(ve)
        }), 400
    except Exception as e:
        current_app.logger.error(f"[UPLOAD_INHOUSE] Schema validation error: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to process file",
            "message": "Schema validation error."
        }), 400

    # 6. Background processing (isolated)
    try:
        current_app.logger.info(f"[UPLOAD_INHOUSE] Data sheet validated rows={len(df)}")
        current_app.logger.info("[UPLOAD_INHOUSE] Launching background upsert thread")
        thread = threading.Thread(target=overwrite_in_background_inhouse_sales, args=(current_app._get_current_object(), df))
        thread.start()
        current_app.logger.debug("[UPLOAD_INHOUSE] Background thread started id=%s", thread.ident)
    except Exception as e:
        current_app.logger.error(f"[UPLOAD_INHOUSE] Failed to start background thread: {e}", exc_info=True)
        return jsonify({
            "error": "Failed to process file",
            "message": "Could not start background processing."
        }), 500

    return jsonify({"message": "File upload received. Processing will continue in the background."}), 200

def overwrite_in_background(app, df):
    with app.app_context():
        try:
            CompetitorSalesStatistics.overwrite_with_dataframe(df)
            current_app.logger.info("Background overwrite complete for CompetitorSalesStatistics.")
        except Exception as e:
            current_app.logger.error(f"Error in background thread CompetitorSalesStatistics: {e}")

def overwrite_in_background_inhouse_sales(app, df):
    with app.app_context():
        try:
            current_app.logger.info(f"Background thread started with DataFrame shape: {df.shape}")
            current_app.logger.info(f"Background thread DataFrame columns: {list(df.columns)}")
            current_app.logger.info(f"Background thread first row: {df.iloc[0].to_dict() if len(df) > 0 else 'No data'}")
            
            InhouseSalesData.upsert_data(df)
            current_app.logger.info("Background overwrite complete for InhouseSalesData.")
        except Exception as e:
            current_app.logger.error(f"Error in background thread InhouseSalesData: {e}", exc_info=True)

@main.route("/upload-sales-statistics", methods=["POST"])
@role_should_be("admin")
def upload_sales_statistics():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(file.filename))
    file.save(filename)

    try:
        df = pd.read_excel(filename,sheet_name="data")

        thread = threading.Thread(target=overwrite_in_background, args=(current_app._get_current_object(), df))
        thread.start()

        return jsonify({"message": "File upload received. Processing will continue in the background."}) , 200

    except Exception as e:
        current_app.logger.error(f"Error processing sales statistics file: {e}")
        return jsonify({"error": "Failed to process file", "message": str(e)}), 500
    
@main.route("/test-staging-upsert", methods=["POST"])
@role_should_be("admin")
def upload_inhouse_sales_staging_upsert():
    current_app.logger.info("In-house sales upload endpoint called.")
    if "file" not in request.files:
        current_app.logger.warning("File part not found in request.")
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        current_app.logger.warning("No file selected.")
        return jsonify({"error": "No selected file"}), 400

    if not file or not allowed_file(file.filename):
        current_app.logger.warning(f"File type not allowed: {file.filename}")
        return jsonify({"error": "File type not allowed"}), 400

    filename = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(file.filename))
    file.save(filename)
    current_app.logger.info(f"File saved to {filename}")

    try:
        df = pd.read_excel(filename, sheet_name="data")
        current_app.logger.info(f"Successfully read {len(df)} rows from Excel file.")

        # expected_cols = {
        #     'year': 'int64',
        #     'month': 'int64',
        #     'manager_name': 'object',
        #     'store_code': 'object',
        #     'store_name': 'object',
        #     'brand_name': 'object',
        #     'amount': 'float64',
        #     'comp': 'object',
        #     'comment': 'object',
        #     'store_category': 'object'
        # }

        # cols_errors = validate_columns(df, expected_cols)
        # if cols_errors:
        #     current_app.logger.error(f"Invalid file format: {cols_errors}")
        #     return jsonify({"error": "Invalid file format", "messages": cols_errors}), 400
        
        current_app.logger.info("File validated successfully. Calling upsert_data.")
        InhouseSalesData.upsert_with_staging(df)
        current_app.logger.info("upsert_data completed.")

        return jsonify({"message": f"Successfully upserted {len(df)} records."}) , 200

    except Exception as e:
        current_app.logger.error(f"Error processing in-house sales file: {e}", exc_info=True)
        return jsonify({"error": "Failed to process file", "message": str(e)}), 500

@main.route("/upsert-inhouse-sales", methods=["POST"])
# @role_should_be("admin")
async def upsert_inhouse_sales():
    current_app.logger.info("In-house sales upload endpoint called.")
    if "file" not in request.files:
        current_app.logger.warning("File part not found in request.")
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        current_app.logger.warning("No file selected.")
        return jsonify({"error": "No selected file"}), 400

    if not file or not allowed_file(file.filename):
        current_app.logger.warning(f"File type not allowed: {file.filename}")
        return jsonify({"error": "File type not allowed"}), 400

    filename = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(file.filename))
    file.save(filename)
    current_app.logger.info(f"File saved to {filename}")

    try:
        df = pd.read_excel(filename, sheet_name="data")
        current_app.logger.info(f"Successfully read {len(df)} rows from Excel file.")
        
        # Debug: Log DataFrame info immediately after reading
        current_app.logger.info(f"Excel DataFrame shape: {df.shape}")
        current_app.logger.info(f"Excel DataFrame columns: {list(df.columns)}")
        current_app.logger.info(f"Excel DataFrame dtypes:\n{df.dtypes}")
        current_app.logger.info(f"Excel DataFrame first row:\n{df.iloc[0] if len(df) > 0 else 'No data'}")
        
        # Check for null values
        null_summary = df.isnull().sum()
        current_app.logger.info(f"Null values per column:\n{null_summary}")
        
        current_app.logger.info("File validated successfully. Calling upsert_data.")
        thread = threading.Thread(target=overwrite_in_background_inhouse_sales, args=(current_app._get_current_object(), df))
        thread.start()

        return jsonify({"message": "File upload received. Processing will continue in the background."}) , 200

    except Exception as e:
        current_app.logger.error(f"Error processing in-house sales file: {e}", exc_info=True)
        return jsonify({"error": "Failed to process file", "message": str(e)}), 500


def overwrite_in_background_inhouse_sales_test(app, df, chunk_size=500, max_workers=4):
    """
    Background function to upsert a large DataFrame in parallel threads for faster DB writes.
    Splits the DataFrame into chunks and processes each chunk in a separate thread.
    Args:
        app: Flask app context for DB access.
        df: pandas DataFrame to upsert.
        chunk_size: Number of rows per chunk (default 500).
        max_workers: Number of parallel threads (default 4).
    """
    with app.app_context():
        try:
            n = len(df)
            # Split DataFrame into chunks of chunk_size rows
            chunks = [df.iloc[i:i+chunk_size] for i in range(0, n, chunk_size)]
            current_app.logger.info(f"Starting parallel upsert: {len(chunks)} chunks, {chunk_size} rows each (last may be smaller). Using {max_workers} workers.")

            def upsert_chunk(chunk):
                """Upsert a single chunk of the DataFrame, with its own app context."""
                with app.app_context():
                    InhouseSalesData.upsert_data_rs(chunk)

            # Use ThreadPoolExecutor to process chunks in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(upsert_chunk, chunk) for chunk in chunks]
                # Wait for all threads to complete and log any exceptions
                for future in concurrent.futures.as_completed(futures):
                    exc = future.exception()
                    if exc:
                        current_app.logger.error(f"Error in chunk upsert: {exc}")
            current_app.logger.info("Parallel background overwrite complete for InhouseSalesData.")
        except Exception as e:
            current_app.logger.error(f"Error in background thread InhouseSalesData: {e}")
