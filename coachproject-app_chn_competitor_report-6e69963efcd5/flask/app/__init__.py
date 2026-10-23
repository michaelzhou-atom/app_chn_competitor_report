import os
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_caching import Cache
from urllib.parse import quote_plus
from .controllers import register_blueprints
from .models import db, initialize_settings
from .helpers import get_db_secret, get_airflow_secret, get_rds_db_secret


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)


def create_app():
    app = Flask(__name__)

    CORS(app)

    # Setup basic configurations from config.py
    app.config.from_object("config.AppConfig")

    # Register blueprints (controllers)
    register_blueprints(app)

    # Get environment variable values
    environment = os.getenv("ENV", "dev")
    aws_database_secret = os.getenv("AWS_DATABASE_SECRET")
    aws_rds_database_secret = os.getenv("AWS_RDS_DATABASE_SECRET")
    aws_database_secret_region = os.getenv("AWS_DATABASE_SECRET_REGION")
    aws_database_host = os.getenv("AWS_DATABASE_HOST")
    aws_database_port = os.getenv("AWS_DATABASE_PORT")
    jwt_secret = os.getenv("JWT_SECRET")
    api_key = os.getenv("API_KEY")
    aws_airflow_secret = os.getenv("AWS_AIRFLOW_SECRET")
    aws_airflow_secret_region = os.getenv("AWS_AIRFLOW_SECRET_REGION")
    aws_airflow_endpoint = os.getenv("AWS_AIRFLOW_ENDPOINT")
    aws_airflow_auth_endpoint = os.getenv("AWS_AIRFLOW_AUTH_ENDPOINT")  # For token-based auth (Airflow 3.0)
    aws_airflow_username = os.getenv(
        "AWS_AIRFLOW_USERNAME" 
    )  # for local environment only
    aws_airflow_password = os.getenv(
        "AWS_AIRFLOW_PASSWORD" 
    )  # for local environment only

    # Setup JWT for auth flow
    app.config["JWT_SECRET"] = jwt_secret
    app.config["API_KEY_VALUE"] = api_key
    app.config["AWS_AIRFLOW_ENDPOINT"] = aws_airflow_endpoint
    app.config["AWS_AIRFLOW_AUTH_ENDPOINT"] = aws_airflow_auth_endpoint

    # Airflow creds for local
    app.config["AWS_AIRFLOW_USERNAME"] = aws_airflow_username
    app.config["AWS_AIRFLOW_PASSWORD"] = aws_airflow_password

    # Database for local
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        basedir, "database\\app.sqlite"
    )

    if environment != "localhost":
        # connect to database
        username, password = get_db_secret(
            aws_database_secret, aws_database_secret_region
        )
        dbname = "competitor_app"

        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"postgresql://{username}:{password}@{aws_database_host}:{aws_database_port}/{dbname}"
        )
        logging.info(f"PostgreSQL Connection String: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # connect to redshift database
        rs_user, rs_password, rs_host, rs_port, rs_dbname = get_rds_db_secret(
            aws_rds_database_secret, aws_database_secret_region
        )
        
        environment = environment.lower()
        encoded_password = quote_plus(rs_password)
        logging.debug(f"Redshift Connection String with encoded password: redshift+psycopg2://{rs_user}:{encoded_password}@{rs_host}:{rs_port}/{environment}_ind360")
        app.config["SQLALCHEMY_BINDS"] = {
            "redshift": f"redshift+psycopg2://{rs_user}:{encoded_password}@{rs_host}:{rs_port}/{environment}_ind360"
        }

        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = (
            False  # Disable track modifications to save resources
        )

        # Airflow creds from AWS secret
        username, password = get_airflow_secret(
            aws_airflow_secret, aws_airflow_secret_region
        )
        app.config["AWS_AIRFLOW_USERNAME"] = username
        app.config["AWS_AIRFLOW_PASSWORD"] = password

    # Initialize the database
    db.init_app(app)
    # migrate.init_app(app, db)
    # Initialize the database and create tables
    with app.app_context():
        db.create_all()
        initialize_settings()

    # Initialize the cache
    app.cache = Cache(app)

    return app