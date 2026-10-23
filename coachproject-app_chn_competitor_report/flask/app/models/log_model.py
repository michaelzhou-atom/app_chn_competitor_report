import pandas as pd
from .db import db
from datetime import datetime
from zoneinfo import ZoneInfo

# logs data
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
#     "update_date": "object"
# }


def shanghai_time():
    return datetime.now(ZoneInfo("Asia/Shanghai"))  # or pytz.timezone("Asia/Shanghai")


class LogData(db.Model):
    __tablename__ = "competitor_sales_collection_log"

    # Composite primary key
    store_code = db.Column(db.String(256), primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(256), primary_key=True)
    store_category = db.Column(db.String(256), primary_key=True)
    update_date = db.Column(db.DateTime, default=shanghai_time, primary_key=True)

    # Other columns
    store_name = db.Column(db.String(256), nullable=False)
    manager_name = db.Column(db.String(256), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    comp = db.Column(db.String(256), nullable=True)
    comment = db.Column(db.String(256), nullable=True)

    @staticmethod
    def bulk_insert(df):
        try:
            # Convert the DataFrame into a list of dictionaries
            data_dict = df.to_dict(orient="records")

            # Bulk insert the data into the SalesData table
            db.session.bulk_insert_mappings(LogData, data_dict)
            db.session.commit()

            return f"Successfully inserted {len(data_dict)} rows."

        except Exception as e:
            # If any error occurs, rollback the session
            db.session.rollback()
            return f"An error occurred: {str(e)}"

    @staticmethod
    def get_all_data(date_from, date_to):
        logs_data = LogData.query.filter(
            LogData.update_date >= date_from,
            LogData.update_date <= date_to,
        ).order_by(LogData.update_date.desc()).all()

        data = [
            {
                "year": log.year,
                "month": log.month,
                "manager_name": log.manager_name,
                "store_code": log.store_code,
                "store_name": log.store_name,
                "brand_name": log.brand_name,
                "amount": log.amount,
                "comp": log.comp,
                "comment": log.comment,
                "store_category": log.store_category,
                "update_date": log.update_date,
            }
            for log in logs_data
        ]

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
                "update_date",
            ],
        )
        return df
