from .db import db
import numpy as np
import pandas as pd
import logging
from flask import current_app
from sqlalchemy import Table, Column, String, MetaData, Numeric, Date, text
from ..helpers.s3_client import s3_client

class cohpure_clr_sku_list:
    _schema = 'landing'
    _table_name = 'cohpure_clr_sku_list'
    _bind_key = 'redshift'
    
    # Manually define the table structure for SQLAlchemy Core
    _metadata = MetaData()
    _table = Table(
        _table_name,
        _metadata,
        Column('store_code', String(256)),
        Column('cal_date', Date),
        Column('clr_pce_ss_ttl_amt_lcl', Numeric(16,2)),
        schema=_schema
    )

    @staticmethod
    def overwrite_in_background(app, df):
        with app.app_context():
            try:
                cohpure_clr_sku_list.overwrite_with_dataframe(df)
                current_app.logger.info("Background overwrite complete for cohpure_clr_sku_list.")
            except Exception as e:
                current_app.logger.error(f"Error in background thread cohpure_clr_sku_list: {e}")

    @staticmethod
    def overwrite_with_dataframe(df):
        """
        Overwrites the table using a direct engine connection, deleting all existing
        data and inserting the new data from the DataFrame.
        """
        log = logging.getLogger(__name__)
        log.info(f"Starting direct overwrite for {len(df)} rows into cohpure_clr_sku_list.")
        
        engine = db.engines[cohpure_clr_sku_list._bind_key]
        table = cohpure_clr_sku_list._table

        # Drop unnamed columns if they exist
        columns_to_drop = [col for col in df.columns if 'Unnamed' in col]
        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)
            log.info(f"Dropped unnamed columns: {columns_to_drop}")

        # Replace empty values with None for database compatibility
        df = df.replace({np.nan: None})
        
        # Ensure cal_date is in proper datetime format for Date column type
        if 'cal_date' in df.columns:
            log.info(f"Before cal_date conversion - sample values: {df['cal_date'].head().tolist()}")
            log.info(f"Before cal_date conversion - dtype: {df['cal_date'].dtype}")
            
            # Convert to datetime if not already, keep as datetime for Date column
            if df['cal_date'].dtype != 'datetime64[ns]':
                df['cal_date'] = pd.to_datetime(df['cal_date'], errors='coerce')
            
            # Convert to date (remove time component) for proper Date storage
            df['cal_date'] = df['cal_date'].dt.date
            
            log.info(f"After cal_date conversion - sample values: {df['cal_date'].head().tolist()}")
            log.info(f"After cal_date conversion - dtype: {df['cal_date'].dtype}")
        
        log.info(f"Final data sample before insertion: {df.head().to_dict('records') if len(df) > 0 else 'No data'}")
        

        # Optimized upsert logic using staging table and bulk operations
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with engine.connect() as con:
                    with con.begin():
                        log.info(f"Beginning optimized upsert (attempt {attempt + 1}/{max_retries}): {engine.url}")

                        # Check if table exists, create if it doesn't
                        if not engine.dialect.has_table(engine.connect(), table.name, schema=table.schema):
                            log.info(f"Table {table.fullname} does not exist. Creating table...")
                            # Create table with distribution key for better performance
                            create_sql = f"""
                            CREATE TABLE IF NOT EXISTS {table.schema}.{table.name} (
                                store_code VARCHAR(256),
                                cal_date DATE,
                                clr_pce_ss_ttl_amt_lcl NUMERIC(16,2),
                                PRIMARY KEY(store_code, cal_date)
                            ) DISTKEY(store_code) SORTKEY(store_code, cal_date);
                            """
                            con.execute(text(create_sql))
                            log.info(f"Table {table.fullname} created successfully with distribution and sort keys.")

                        # Create staging table optimized for bulk load
                        staging_table = f"#stage_{table.name}_{attempt}"
                        create_stage_sql = f"""
                        CREATE TEMPORARY TABLE {staging_table} (
                            store_code VARCHAR(256) ENCODE lzo,
                            cal_date DATE ENCODE raw,
                            clr_pce_ss_ttl_amt_lcl NUMERIC(16,2) ENCODE raw
                        ) DISTSTYLE KEY DISTKEY(store_code) COMPOUND SORTKEY(store_code, cal_date);
                        """
                        con.execute(text(create_stage_sql))
                        log.info(f"Created staging table: {staging_table}")

                        # Upload DataFrame to S3 and get COPY command
                        s3_result = s3_client.upload_dataframe(
                            df,
                            file_prefix=f'{table.name}'
                        )
                        
                        # Format and execute COPY command
                        copy_cmd = s3_result['copy_command'].format(
                            table_name=staging_table,
                            columns='store_code, cal_date, clr_pce_ss_ttl_amt_lcl'
                        )
                        
                        con.execute(text(copy_cmd))
                        log.info(f"Loaded {len(df)} rows using COPY command. S3 file: s3://{s3_result['bucket']}/{s3_result['key']}")

                        # Perform efficient merge operation using compound key
                        merge_sql = f"""
                        -- Update existing records
                        UPDATE {table.schema}.{table.name} t
                        SET clr_pce_ss_ttl_amt_lcl = s.clr_pce_ss_ttl_amt_lcl
                        FROM {staging_table} s
                        WHERE t.store_code = s.store_code 
                        AND t.cal_date = s.cal_date;

                        -- Insert new records that don't exist in the target table
                        INSERT INTO {table.schema}.{table.name}
                        (store_code, cal_date, clr_pce_ss_ttl_amt_lcl)
                        SELECT s.store_code, s.cal_date, s.clr_pce_ss_ttl_amt_lcl
                        FROM {staging_table} s
                        LEFT JOIN {table.schema}.{table.name} t
                        ON t.store_code = s.store_code 
                        AND t.cal_date = s.cal_date
                        WHERE t.store_code IS NULL;
                        """
                        con.execute(text(merge_sql))
                        log.info("Completed merge operation")

                        # Clean up staging table
                        con.execute(text(f"DROP TABLE {staging_table}"))
                        log.info(f"Dropped staging table")
                        
                        log.info("Transaction committed successfully")
                        break  # Success, exit retry loop
                    
            except Exception as e:
                log.error(f"Error during upsert (attempt {attempt + 1}/{max_retries}): {e}", exc_info=True)
                if attempt == max_retries - 1:  # Last attempt
                    raise e
                else:
                    log.info(f"Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
        log.info("Overwrite process finished.")