import pandas as pd
from .db import db
from sqlalchemy import func

# list data
# {
#     "store": "object",
#     "store_name": "object",
#     "manager": "object",
#     "year": "int64",
#     "month": "int64",
#     "brand": "object",
#     "store_category": "object",
#     "status": "object",
#     "manager_code": "object",
#     "brand_code": "object",
# }


# Add the models here
class ListData(db.Model):
    __tablename__ = "list_data"

    # Define a composite primary key using multiple columns
    store = db.Column(db.String(256), primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(256), primary_key=True)
    store_category = db.Column(db.String(256), primary_key=True)

    store_name = db.Column(db.String(256), nullable=False)
    manager = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(256), nullable=False)
    manager_code = db.Column(db.String(256), nullable=False)
    brand_code = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f"<ListData {self.store} - {self.year}-{self.month}>"

    @staticmethod
    def fetch_all_data():
        list_data = ListData.query.all()

        data = [
            {
                "store": sale.store,
                "store_name": sale.store_name,
                "manager": sale.manager,
                "year": sale.year,
                "month": sale.month,
                "brand": sale.brand,
                "store_category": sale.store_category,
                "status": sale.status,
                "manager_code": sale.manager_code,
                "brand_code": sale.brand_code,
            }
            for sale in list_data
        ]

        # Convert the list of dictionaries into a DataFrame
        df = pd.DataFrame(
            data,
            columns=[
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
            ],
        )
        return df


    @staticmethod
    def delete_and_insert(df):

        try:
            with db.session.begin():
                db.session.query(ListData).delete(synchronize_session=False)

                data_dict = df.to_dict(orient="records")
                db.session.bulk_insert_mappings(ListData, data_dict)

                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


    @staticmethod
    def year_and_month():
        result = db.session.query(
            ListData.year,
            ListData.month,
            func.count().label('count')  # Count the number of entries for each year and month
        ).group_by(
            ListData.year,
            ListData.month
        ).order_by(
            func.count().desc()  # Sort by count in descending order
        ).all()
        
        
        data = []
        for row in result:
            data.append({'year': row.year, 'month': row.month, 'count': row.count})
            
        return data
