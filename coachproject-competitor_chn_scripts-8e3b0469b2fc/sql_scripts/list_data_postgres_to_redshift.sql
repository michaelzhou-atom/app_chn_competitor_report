TRUNCATE TABLE landing.list_data;

COPY landing.list_data
FROM 's3://{bucket}/competitor_app_scripts/stage/list_data.csv' 
IAM_ROLE '{iam_role}'
FORMAT AS CSV IGNOREHEADER 1;