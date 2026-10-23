TRUNCATE TABLE landing.competitor_sales_collection_log;

COPY landing.competitor_sales_collection_log
FROM 's3://{bucket}/competitor_app_scripts/stage/competitor_sales_collection_log.csv' 
IAM_ROLE '{iam_role}'
FORMAT AS CSV IGNOREHEADER 1;