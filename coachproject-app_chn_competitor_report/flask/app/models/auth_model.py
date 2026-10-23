from sqlalchemy import text
from .db import db


class Auth(db.Model):
    __tablename__ = "auth"

    username = db.Column(db.String(100), nullable=False, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(1000), nullable=False)

    @staticmethod
    def get_creds(username):
        creds = Auth.query.filter(
            Auth.username == username,
        ).first()

        if creds == None:
            raise "User not found"

        return creds

    @staticmethod
    def insert_user(username, password, role):

        try:
            data = {"username": username, "password": password, "role": role}
            new_record = Auth(**data)
            db.session.add(new_record)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_password(username, password, role):

        try:
            existing_record = (
                db.session.query(Auth)
                .filter_by(
                    username=username,
                    role=role,
                )
                .first()
            )

            if existing_record:
                # Update the existing record
                existing_record.password = password
                db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise e


