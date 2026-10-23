from .db import db
import pandas as pd
import numpy as np
import logging
from sqlalchemy import Table, Column, Integer, String, Numeric, MetaData

class CompetitorSalesStatistics:
    _schema = 'landing'
    _table_name = 'competitor_sales_statistics_store_nbr_monthly'
    _bind_key = 'redshift'
    
    # Manually define the table structure for SQLAlchemy Core
    _metadata = MetaData()
    _table = Table(
        _table_name,
        _metadata,
        Column('year', Integer),
        Column('month', Integer),
        Column('brand_name', String(256)),
        Column('total_store_count_ty', Integer),
        Column('total_store_count_ly', Integer),
        Column('net_opening', Integer),
        Column('total_store_count_growth', Numeric(10, 10)),
        Column('store_category', String(256)),
        schema=_schema
    )

    @staticmethod
    def overwrite_with_dataframe(df):
        """
        Overwrites the table using a direct engine connection, deleting all existing
        data and inserting the new data from the DataFrame.
        """
        log = logging.getLogger(__name__)
        log.info(f"Starting direct overwrite for {len(df)} rows into CompetitorSalesStatistics.")
        
        engine = db.engines[CompetitorSalesStatistics._bind_key]
        table = CompetitorSalesStatistics._table

        # Drop unnamed columns if they exist
        columns_to_drop = [col for col in df.columns if 'Unnamed' in col]
        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)
            log.info(f"Dropped unnamed columns: {columns_to_drop}")

        with engine.connect() as con:
            with con.begin() as transaction:
                try:
                    log.info(f"Beginning transaction on engine: {engine.url}")
                    
                    log.info(f"Deleting all rows from {table.fullname}...")
                    con.execute(table.delete())
                    log.info("Delete complete.")

                    # Replace nan with None for db
                    df =df.replace({np.nan: None})
                    
                    data_dict = df.to_dict(orient="records")
                    
                    log.info(f"Bulk inserting {len(data_dict)} new rows...")
                    con.execute(table.insert(), data_dict)
                    log.info("Bulk insert complete.")
                    
                    log.info("Committing transaction...")
                except Exception as e:
                    log.error(f"Error during direct overwrite: {e}", exc_info=True)
                    raise e
        log.info("Overwrite process finished.")