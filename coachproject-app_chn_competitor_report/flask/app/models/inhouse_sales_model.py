from .db import db
from sqlalchemy import Integer, String, Numeric, text
from sqlalchemy.schema import CreateTable
import pandas as pd
import numpy as np
import logging
from io import StringIO
import csv
from ..helpers.s3_client import s3_client

def psql_insert_copy(table, conn, keys, data_iter):
    """
    Custom method for pandas.to_sql to perform a fast bulk insert using psycopg2's copy_from.
    This is required for Redshift as the default pandas method is not compatible.
    """
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        # Use to_csv to ensure proper data formatting for Redshift
        pd.DataFrame(data_iter, columns=keys).to_csv(s_buf, header=False, index=False, quoting=csv.QUOTE_MINIMAL)
        s_buf.seek(0)

        table_name = f'"{table.schema}"."{table.name}"'
        sql = f'COPY {table_name} FROM STDIN WITH CSV'
        cur.copy_expert(sql=sql, file=s_buf)

class InhouseSalesData(db.Model):
    __bind_key__ = 'redshift'
    __tablename__ = 'inhouse_sales_data_collection'
    __table_args__ = {'schema': 'landing'}

    year = db.Column(Integer, primary_key=True, nullable=False)
    month = db.Column(Integer, primary_key=True, nullable=False)
    manager_name = db.Column(String(256), nullable=True)
    store_code = db.Column(String(256), primary_key=True, nullable=False)
    store_name = db.Column(String(256), nullable=True)
    brand_name = db.Column(String(256), primary_key=True, nullable=False)
    amount = db.Column(Numeric(14, 2), nullable=True)
    comp = db.Column(String(256), nullable=True)
    comment = db.Column(String(256), nullable=True)
    store_category = db.Column(String(256), nullable=True)

    def __repr__(self):
        return f"<InhouseSalesData {self.year}-{self.month} {self.store_code} {self.brand_name}>"

    @staticmethod
    def fetch_all_data():
        """Fetches all records from the table and returns as a pandas DataFrame."""
        engine = db.engines['redshift']
        with engine.connect() as con:
            df = pd.read_sql_table(InhouseSalesData.__tablename__, con, schema=InhouseSalesData.__table_args__['schema'])
        return df

    @staticmethod
    def upsert_data(df):
        """
        Upserts data using S3 COPY and staging table pattern - optimized for Redshift.
        Follows the same high-performance pattern as cohpure_clr_sku_list.
        Composite primary key: (year, month, store_code, brand_name)
        """
        log = logging.getLogger(__name__)
        log.info(f"Starting S3 COPY upsert for {len(df)} rows into InhouseSalesData.")
        
        engine = db.engines['redshift']
        table = InhouseSalesData.__table__
        
        # Data preparation
        log.info("Preparing DataFrame...")
        
        # Drop unnamed columns
        columns_to_drop = [col for col in df.columns if 'Unnamed' in str(col)]
        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)
            log.info(f"Dropped unnamed columns: {columns_to_drop}")
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower()
        log.info(f"Normalized columns: {list(df.columns)}")
        
        # Validate required columns
        required_columns = ['year', 'month', 'store_code', 'brand_name']
        missing_required = [col for col in required_columns if col not in df.columns]
        if missing_required:
            raise ValueError(f"Missing required columns: {missing_required}")
        
        # Clean data - replace NaN with None for proper NULL handling
        df = df.replace({np.nan: None})
        
        # Ensure proper data types
        df['year'] = df['year'].astype(int)
        df['month'] = df['month'].astype(int)
        
        # Select only expected columns in the correct order
        expected_columns = ['year', 'month', 'manager_name', 'store_code', 'store_name', 
                           'brand_name', 'amount', 'comp', 'comment', 'store_category']
        df_final = df[[col for col in expected_columns if col in df.columns]]
        
        log.info(f"Final DataFrame shape: {df_final.shape}")
        log.info(f"Sample data: {df_final.head(2).to_dict('records')}")
        
        # Optimized upsert with staging table and S3 COPY
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with engine.connect() as con:
                    with con.begin():
                        log.info(f"Beginning S3 COPY upsert (attempt {attempt + 1}/{max_retries})")
                        
                        # Check if target table exists
                        if not engine.dialect.has_table(con, table.name, schema=table.schema):
                            log.info(f"Table {table.fullname} does not exist. Creating table...")
                            create_sql = f"""
                            CREATE TABLE IF NOT EXISTS {table.schema}.{table.name} (
                                year INTEGER,
                                month INTEGER,
                                manager_name VARCHAR(256),
                                store_code VARCHAR(256),
                                store_name VARCHAR(256),
                                brand_name VARCHAR(256),
                                amount NUMERIC(14,2),
                                comp VARCHAR(256),
                                comment VARCHAR(256),
                                store_category VARCHAR(256),
                                PRIMARY KEY(year, month, store_code, brand_name)
                            ) DISTKEY(store_code) SORTKEY(year, month, store_code, brand_name);
                            """
                            con.execute(text(create_sql))
                            log.info("Table created successfully with distribution and sort keys.")
                        
                        # Create temporary staging table
                        staging_table = f"#stage_{table.name}_{attempt}"
                        create_stage_sql = f"""
                        CREATE TEMPORARY TABLE {staging_table} (
                            year INTEGER ENCODE az64,
                            month INTEGER ENCODE az64,
                            manager_name VARCHAR(256) ENCODE lzo,
                            store_code VARCHAR(256) ENCODE lzo,
                            store_name VARCHAR(256) ENCODE lzo,
                            brand_name VARCHAR(256) ENCODE lzo,
                            amount NUMERIC(14,2) ENCODE az64,
                            comp VARCHAR(256) ENCODE lzo,
                            comment VARCHAR(256) ENCODE lzo,
                            store_category VARCHAR(256) ENCODE lzo
                        ) DISTSTYLE KEY DISTKEY(store_code) COMPOUND SORTKEY(year, month, store_code, brand_name);
                        """
                        con.execute(text(create_stage_sql))
                        log.info(f"Created staging table: {staging_table}")
                        
                        # Upload DataFrame to S3 and get COPY command
                        s3_result = s3_client.upload_dataframe(
                            df_final,
                            file_prefix=f'{table.name}'
                        )
                        
                        # Build column list for COPY command
                        columns_list = ', '.join(df_final.columns)
                        
                        # Format and execute COPY command
                        copy_cmd = s3_result['copy_command'].format(
                            table_name=staging_table,
                            columns=columns_list
                        )
                        
                        con.execute(text(copy_cmd))
                        log.info(f"Loaded {len(df_final)} rows using COPY command. S3: s3://{s3_result['bucket']}/{s3_result['key']}")
                        
                        # Perform merge operation (upsert) using composite key
                        merge_sql = f"""
                        -- Update existing records
                        UPDATE {table.schema}.{table.name} t
                        SET 
                            manager_name = s.manager_name,
                            store_name = s.store_name,
                            amount = s.amount,
                            comp = s.comp,
                            comment = s.comment,
                            store_category = s.store_category
                        FROM {staging_table} s
                        WHERE t.year = s.year 
                        AND t.month = s.month
                        AND t.store_code = s.store_code 
                        AND t.brand_name = s.brand_name;

                        -- Insert new records that don't exist
                        INSERT INTO {table.schema}.{table.name}
                        ({columns_list})
                        SELECT s.year, s.month, s.manager_name, s.store_code, s.store_name, s.brand_name, s.amount, s.comp, s.comment, s.store_category
                        FROM {staging_table} s
                        LEFT JOIN {table.schema}.{table.name} t
                        ON t.year = s.year 
                        AND t.month = s.month
                        AND t.store_code = s.store_code 
                        AND t.brand_name = s.brand_name
                        WHERE t.year IS NULL;
                        """
                        con.execute(text(merge_sql))
                        log.info("Merge operation completed successfully")
                        
                        # Clean up staging table
                        con.execute(text(f"DROP TABLE {staging_table}"))
                        log.info("Staging table dropped")
                        
                        log.info("Transaction committed successfully")
                        break  # Success - exit retry loop
                        
            except Exception as e:
                log.error(f"Error during S3 COPY upsert (attempt {attempt + 1}/{max_retries}): {e}", exc_info=True)
                if attempt == max_retries - 1:
                    raise e
                log.info(f"Retrying... ({attempt + 2}/{max_retries})")
        
        log.info("Upsert process finished successfully.")

    @staticmethod
    def upsert_with_staging(df):
        """
        Upserts data using a staging table and the Redshift COPY command.
        This is the most performant and recommended method for bulk upserts.
        """
        log = logging.getLogger(__name__)
        log.info(f"Starting Redshift COPY upsert for {len(df)} rows into InhouseSalesData.")
        
        engine = db.engines['redshift']
        staging_table_name = 'inhouse_sales_data_collection'
        staging_schema = 'cr'
        target_table = InhouseSalesData.__tablename__
        target_schema = InhouseSalesData.__table_args__['schema']
        
        staging_table_obj = InhouseSalesData.__table__.tometadata(db.metadata, schema=staging_schema, name=staging_table_name)

        with engine.connect() as con:
            try:
                log.info(f"Dropping staging table {staging_schema}.{staging_table_name} if it exists...")
                con.execute(text(f'DROP TABLE IF EXISTS {staging_schema}.{staging_table_name}'))
                
                log.info(f"Creating staging table {staging_schema}.{staging_table_name}...")
                con.execute(CreateTable(staging_table_obj))

                log.info("Streaming data into staging table via COPY...")
                df.to_sql(
                    name=staging_table_name,
                    con=con,
                    schema=staging_schema,
                    if_exists='append',
                    index=False,
                    method=psql_insert_copy
                )

                with con.begin() as transaction:
                    log.info("Beginning transaction for upsert...")
                    delete_sql = text(f"""
                        DELETE FROM {target_schema}.{target_table}
                        USING {staging_schema}.{staging_table_name}
                        WHERE {target_schema}.{target_table}.year = {staging_schema}.{staging_table_name}.year
                          AND {target_schema}.{target_table}.month = {staging_schema}.{staging_table_name}.month
                          AND {target_schema}.{target_table}.store_code = {staging_schema}.{staging_table_name}.store_code
                          AND {target_schema}.{target_table}.brand_name = {staging_schema}.{staging_table_name}.brand_name;
                    """)
                    con.execute(delete_sql)

                    insert_sql = text(f"""
                        INSERT INTO {target_schema}.{target_table}
                        SELECT * FROM {staging_schema}.{staging_table_name};
                    """)
                    con.execute(insert_sql)
                log.info("Transaction committed successfully.")

            except Exception as e:
                log.error(f"Error during Redshift COPY upsert: {e}", exc_info=True)
                raise e
            finally:
                log.info(f"Dropping staging table: {staging_schema}.{staging_table_name}")
                con.execute(text(f'DROP TABLE IF EXISTS {staging_schema}.{staging_table_name}'))
                log.info("Staging table dropped.")

    @staticmethod
    def upsert_data_rs(df):
        """
        Row-wise upsert for Redshift using composite key (year, month, store_code, brand_name):
        If a record exists, update it; otherwise, insert a new record. No staging table is used.
        """
        log = logging.getLogger(__name__)
        log.info(f"Starting row-wise upsert for {len(df)} rows using Redshift engine connection.")

        engine = db.engines['redshift']
        Session = db.sessionmaker(bind=engine)
        session = Session()
        try:
            for data in df.to_dict(orient="records"):
                # Check if record exists using composite key
                existing = session.query(InhouseSalesData).filter_by(
                    year=data["year"],
                    month=data["month"],
                    store_code=data["store_code"],
                    brand_name=data["brand_name"]
                ).first()
                if existing:
                    # Update fields
                    for col in ["manager_name", "store_name", "amount", "comp", "comment", "store_category"]:
                        setattr(existing, col, data.get(col))
                else:
                    # Insert new record
                    new_row = InhouseSalesData(**data)
                    session.add(new_row)
            session.commit()
            log.info("Row-wise upsert complete and committed.")
        except Exception as e:
            session.rollback()
            log.error(f"Error during row-wise upsert: {e}", exc_info=True)
            raise e
        finally:
            session.close()