COPY landing.competitor_sales_data_collection
FROM 's3://{bucket}/competitor_app_scripts/stage/competitor_sales.csv' 
IAM_ROLE '{iam_role}'
FORMAT AS CSV IGNOREHEADER 1;