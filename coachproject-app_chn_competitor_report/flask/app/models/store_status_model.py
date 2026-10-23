from .db import db


# sales data
# {
#     "store_code": "object",
#     "store_name": "object",
#     "manager_name": "object",
#     "year": "int64",
#     "month": "int64",
#     "brand_name": "object",
#     "store_category": "object",
#     "status": "object",
# }


# create or replace TABLE COMPETITOR_SALES_COLLECTION_STORE_STATUS (
# 	STORE_CODE VARCHAR(256),
# 	STORE_NAME VARCHAR(256),
# 	MANAGER_NAME VARCHAR(256),
# 	YEAR NUMBER(4,0),
# 	MONTH NUMBER(2,0),
# 	BRAND_NAME VARCHAR(256),
# 	STORE_CATEGORY VARCHAR(256),
# 	STATUS VARCHAR(256)
# );



class StoreStatus(db.Model):
    __tablename__ = "competitor_sales_collection_store_status"

    # Composite primary key
    store_code = db.Column(db.String(256), primary_key=True)
    year = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(256), primary_key=True)

    # Other cols
    store_name = db.Column(db.String(256), nullable=False)
    manager_name = db.Column(db.String(256), nullable=False)
    store_category = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(256), nullable=False)

    @staticmethod
    def upsert_data(df):
        try:
            # Insert or update data
            data_dict = df.to_dict(orient="records")
            for data in data_dict:
                # Check if record already exists
                existing_record = (
                    db.session.query(StoreStatus)
                    .filter_by(
                        store_code=data["store_code"],
                        year=data["year"],
                        month=data["month"],
                        brand_name=data["brand_name"],
                    )
                    .first()
                )

                if existing_record:
                    # Update the existing record
                    existing_record.store_name = data["store_name"]
                    existing_record.manager_name = data["manager_name"]
                    existing_record.store_category = data["store_category"]
                    existing_record.status = data["status"]
                    
                else:
                    
                    # Insert new record if not exists
                    new_record = StoreStatus(**data)
                    db.session.add(new_record)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"An error occurred: {str(e)}")

    def __repr__(self):
        return f"<SalesData {self.store_name} - {self.brand_name} - {self.year}-{self.month}>"
