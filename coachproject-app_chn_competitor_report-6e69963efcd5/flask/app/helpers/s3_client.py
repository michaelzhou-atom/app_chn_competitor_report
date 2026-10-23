import boto3
import logging
import os
import json
from io import StringIO
from datetime import datetime

logger = logging.getLogger(__name__)

class S3Client:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Skip initialization if already done
        if S3Client._initialized:
            return
            
        # Use the default instance role credentials
        self.client = None
        self.bucket = None
        self.prefix = None
        self.region = None
        self.iam_role = None
        S3Client._initialized = True
    
    def initialize(self):
        """Initialize the S3 client with configuration. Called when needed."""
        if self.client is not None:
            return
        
        # Get configuration from environment variables
        self.bucket = os.getenv('AWS_S3_BUCKET')
        if not self.bucket:
            raise ValueError("AWS_S3_BUCKET environment variable must be set")
            
        self.prefix = os.getenv('AWS_S3_PREFIX', 'competitor_app_scripts')
        self.region = os.getenv('AWS_REGION', 'ap-southeast-1')
        
        # Initialize S3 client with explicit region
        # This is critical for AWS China regions
        try:
            self.client = boto3.client('s3', region_name=self.region)
            logger.info(f"Initialized S3 client for region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
        
        # Get environment and set appropriate Redshift role
        env = os.getenv('ENV', 'DEV').upper()
        
        # Get role from environment variables based on environment
        role_env_var = f'REDSHIFT_ROLE_{env}'
        self.iam_role = os.getenv(role_env_var)
        
        if not self.iam_role:
            raise ValueError(f"No Redshift IAM role configured for environment {env}. Set {role_env_var} in .env")
            
        logger.info(f"Using Redshift IAM role for {env}: {self.iam_role}")

    def upload_dataframe(self, df, file_prefix):
        """
        Upload a DataFrame to S3 as CSV and return the S3 path and COPY command
        """
        self.initialize()
        try:
            # Generate unique file name with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f'{file_prefix}_{timestamp}.csv'
            s3_key = f'{self.prefix}/temp/{file_name}'

            # Convert DataFrame to CSV
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False, header=False)
            
            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=csv_buffer.getvalue()
            )
            logger.info(f"Uploaded data to S3: s3://{self.bucket}/{s3_key}")

            # Generate COPY command
            copy_command = f"""
            COPY {{table_name}} ({{columns}})
            FROM 's3://{self.bucket}/{s3_key}'
            IAM_ROLE '{self.iam_role}'
            CSV
            DATEFORMAT 'YYYY-MM-DD'
            TIMEFORMAT 'YYYY-MM-DD HH:MI:SS'
            NULL AS 'null'
            REGION '{self.region}';
            """

            return {
                'bucket': self.bucket,
                'key': s3_key,
                'copy_command': copy_command
            }

        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise


# Create a singleton instance
s3_client = S3Client()