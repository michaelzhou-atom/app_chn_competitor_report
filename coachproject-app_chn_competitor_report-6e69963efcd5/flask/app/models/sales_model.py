import pandas as pd
from .db import db
import logging
from sqlalchemy import text


# sales data
# {
#     "year": "int64",
#     "month": "int64",
#     "manager_name": "object",
#     "store_code": "object",
#     "store_name": "object",
#     "brand_name": "object",
#     "amount": "float64",
#     "comp": "object",
#     "comment": "object",
#     "store_category": "object",
# }


def sales_data_to_df(sales_data):
    data = [
        {
            "year": sale.year,
            "month": sale.month,
            "manager_name": sale.manager_name,
            "store_code": sale.store_code,
            "store_name": sale.store_name,
            "brand_name": sale.brand_name,
            "amount": sale.amount,
            "comp": sale.comp,
            "comment": sale.comment,
            "store_category": sale.store_category,
        }
        for sale in sales_data
    ]

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(
        data,
        columns=[
            "year",
            "month",
            "manager_name",
            "store_code",
            "store_name",
            "brand_name",
            "amount",
            "comp",
            "comment",
            "store_category",
        ],
    )

    return df


class SalesData(db.Model):
    __tablename__ = "competitor_sales_collection"

    # Redshift table configuration for reports
    _schema = 'landing'
    _table_name = 'All_brand_sales_data_collection'
    _bind_key = 'redshift'

    # Composite primary key
    store_code = db.Column(db.String(256), primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(256), primary_key=True)
    store_category = db.Column(db.String(256), primary_key=True)

    # Other columns
    store_name = db.Column(db.String(256), nullable=False)
    manager_name = db.Column(db.String(256), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    comp = db.Column(db.String(256), nullable=True)
    comment = db.Column(db.String(256), nullable=True)

    @staticmethod
    def get_sales_data(year, month, store_code):
        # Fetch sales data where year >= given_year and month = given_month
        sales_data = SalesData.query.filter(
            SalesData.year >= year,
            SalesData.month == month,
            SalesData.store_code == store_code,
            SalesData.brand_name.notin_(
                ["Coach", "Coach (pure)", "Kate Spade", "Stuart Weitzman"]
            ),
        ).all()

        df = sales_data_to_df(sales_data)
        return df

    @staticmethod
    def get_reports_data(start_year, end_year, month, store_category):
        # Fetch sales data from Redshift table using class attributes
        logging.info(f"[GET_REPORTS_DATA] Called with start_year={start_year}, end_year={end_year}, month={month}, store_category={store_category}")
        try:
            # Get Redshift engine using class attribute
            engine = db.engines[SalesData._bind_key]
            logging.info(f"[GET_REPORTS_DATA] Using engine bind key: {SalesData._bind_key}")
            
            # Build table name from class attributes
            full_table_name = f"{SalesData._schema}.{SalesData._table_name}"
            
            # SQL query to fetch data from Redshift
            sql_query = text(f"""
            SELECT 
                year,
                month,
                manager_name,
                store_code,
                store_name,
                brand_name,
                amount,
                comp,
                comment,
                store_category
            FROM {full_table_name}
            WHERE year IN (:start_year, :end_year)
                AND month = :month
                AND store_category = :store_category
            ORDER BY year, store_code, brand_name
            """)
            
            # Execute query using SQLAlchemy connection and convert to DataFrame
            logging.info(f"[GET_REPORTS_DATA] Executing query on table: {full_table_name}")
            logging.info(f"[GET_REPORTS_DATA] Query params: start_year={start_year}, end_year={end_year}, month={month}, store_category={store_category}")
            
            with engine.connect() as connection:
                result = connection.execute(sql_query, {
                    'start_year': start_year,
                    'end_year': end_year,
                    'month': month,
                    'store_category': store_category
                })
                
                # Convert result to DataFrame
                columns = result.keys()
                data = result.fetchall()
                df = pd.DataFrame(data, columns=columns)
            
            # Log results
            logging.info(f"[GET_REPORTS_DATA] {store_category} data for years {start_year}-{end_year}, month={month}")
            logging.info(f"[GET_REPORTS_DATA] Total records fetched: {len(df)}")
            logging.info(f"[GET_REPORTS_DATA] DataFrame shape: {df.shape}")
            if not df.empty:
                logging.info(f"[GET_REPORTS_DATA] Sample data (first 3 rows): {df.head(3).to_dict('records')}")
            else:
                logging.warning(f"[GET_REPORTS_DATA] No data returned for {store_category}!")
            
            return df
            
        except Exception as e:
            logging.error(f"Error fetching data from {full_table_name}: {e}")
            raise e

    @staticmethod
    def delete_and_insert(df, the_year, the_month, store_code):

        try:

            with db.session.begin():
                db.session.query(SalesData).filter(
                    SalesData.year >= the_year,  # Filter by exact year
                    SalesData.month == the_month,
                    SalesData.store_code == store_code,
                    SalesData.brand_name.notin_(
                        ["Coach", "Coach (pure)", "Kate Spade", "Stuart Weitzman"]
                    ),
                ).delete(synchronize_session=False)

                data_dict = df.to_dict(orient="records")
                db.session.bulk_insert_mappings(SalesData, data_dict)

                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def upsert_data(df):
        try:

            # Insert or update data
            data_dict = df.to_dict(orient="records")

            for data in data_dict:
                # Check if record already exists
                existing_record = (
                    db.session.query(SalesData)
                    .filter_by(
                        store_code=data["store_code"],
                        year=data["year"],
                        month=data["month"],
                        brand_name=data["brand_name"],
                        store_category=data["store_category"],
                    )
                    .first()
                )

                if existing_record:
                    # Update the existing record
                    existing_record.store_name = data["store_name"]
                    existing_record.manager_name = data["manager_name"]
                    existing_record.amount = data["amount"]
                    existing_record.comp = data["comp"]
                    existing_record.comment = data["comment"]
                else:
                    # Insert new record if not exists
                    new_record = SalesData(**data)
                    db.session.add(new_record)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"An error occurred: {str(e)}")

    def __repr__(self):
        return f"<SalesData {self.store_name} - {self.brand_name} - {self.year}-{self.month}>"
