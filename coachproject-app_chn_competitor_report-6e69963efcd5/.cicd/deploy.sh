#!/bin/bash

while (( "$#" ));
do
    if [ "$1" == "-b" ] || [ "$1" == "--branch" ] ; then
        BRANCH=$2
    elif [ "$1" == "-r" ] || [ "$1" == "--repo" ] ; then
        REPO=$2
    elif [ "$1" == "-e" ] || [ "$1" == "--email-list" ] ; then
        ADDITIONAL_EMAILS="-e $2"
    elif [ "$1" == "-c" ] || [ "$1" == "--changeset" ] ; then
        OLD_IFS="$IFS"
        IFS=$'\n'
        CHANGESET=($(echo $2 | jq -r '.[]'))
        IFS="$OLD_IFS"
    fi
    shift
done

if [[ -z $BRANCH ]]; then
    echo "Branch (-b) not set"
    exit 1;
fi

if [[ "$BRANCH" == "DEV" ]]; then
    SERVER_IP="10.250.224.159"
    ENV="DEV"
    DATABASE_SECRET=COMPETITORAPP/POSTGRES_DEV
    RDS_DATABASE_SECRET=redshift-copy-credentials
    AIRFLOW_ENDPOINT="https://airflow-chn.analytics.tapestry.com/api/v2/dags/simple_sleep_dag/dagRuns"
    AIRFLOW_AUTH_ENDPOINT="https://airflow-chn.analytics.tapestry.com/auth/token"
    SSH_KEY=""  # No key needed for DEV

elif [[ "$BRANCH" == "QA" ]]; then
    SERVER_IP="10.236.8.31"
    ENV="QA"
    DATABASE_SECRET=COMPETITORAPP/POSTGRES_QA
    RDS_DATABASE_SECRET=tpr-qa-redshift-credentials
    AIRFLOW_ENDPOINT="https://nonprod-airflow-lb01.global.coach.com/airflow/api/v1/dags/competitor_sales_agg_pipeline/dagRuns"
    AIRFLOW_AUTH_ENDPOINT=""  # QA uses Airflow 2.8 - no token auth endpoint
    PASSPHRASE=$(aws secretsmanager get-secret-value --secret-id tpr_jenkins_key --query SecretString --output text)
    SSH_KEY="/var/lib/jenkins/.ssh/id_rsa_decrypted"
    # Decrypt the SSH private key
    openssl enc -aes-256-cbc -d -in /var/lib/jenkins/.ssh/id_rsa.enc -out /var/lib/jenkins/.ssh/id_rsa_decrypted -pass pass:"$PASSPHRASE"
    chmod 600 /var/lib/jenkins/.ssh/id_rsa_decrypted

elif [[ "$BRANCH" == "master" ]]; then
    SERVER_IP="10.236.0.231"
    ENV="PRD"
    DATABASE_SECRET=COMPETITORAPP/POSTGRES_PROD
    RDS_DATABASE_SECRET=tpr-prd-redshift-credentials
    AIRFLOW_ENDPOINT="https://prod-airflow-lb01.global.coach.com/airflow/api/v1/dags/competitor_sales_agg_pipeline/dagRuns"
    AIRFLOW_AUTH_ENDPOINT=""  # PRD uses Airflow 2.8 - no token auth endpoint
    PASSPHRASE=$(aws secretsmanager get-secret-value --secret-id tpr_jenkins_key --query SecretString --output text)
    SSH_KEY="/var/lib/jenkins/.ssh/id_rsa_decrypted"
    # Decrypt the SSH private key
    openssl enc -aes-256-cbc -d -in /var/lib/jenkins/.ssh/id_rsa.enc -out /var/lib/jenkins/.ssh/id_rsa_decrypted -pass pass:"$PASSPHRASE"
    chmod 600 /var/lib/jenkins/.ssh/id_rsa_decrypted

else
    echo "Branch $BRANCH is not configured for deployment."
    exit 1
fi

# Fetch DB config from Secrets Manager
SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id "$DATABASE_SECRET" \
    --output json | jq -r .SecretString)

DB_HOST=$(echo "$SECRET_JSON" | jq -r '.host')
DB_PORT=$(echo "$SECRET_JSON" | jq -r '.port')
DB_REGION=$(echo "$SECRET_JSON" | jq -r '.region')
API_KEY=$(echo "$SECRET_JSON" | jq -r '.api_key')

# Create .env File (locally)
create_env_file() {
    # Set S3 bucket based on environment
    if [[ "$ENV" == "DEV" ]]; then
        S3_BUCKET="334242416958-eds-dev-ap-southeast-1"
        REDSHIFT_ROLE="arn:aws:iam::334242416958:role/service-role/AmazonRedshift-CommandsAccessRole-20230523T195747"
        AWS_REGION="ap-southeast-1"
    elif [[ "$ENV" == "QA" ]]; then
        S3_BUCKET="175826060701-eds-qa-cn-north-1"
        REDSHIFT_ROLE="arn:aws-cn:iam::175826060701:role/datalab-cn-redshift-qa-cn-north-1-role"
        AWS_REGION="cn-north-1"
    elif [[ "$ENV" == "PRD" ]]; then
        S3_BUCKET="175814205108-eds-prd-cn-north-1"
        REDSHIFT_ROLE="arn:aws-cn:iam::175814205108:role/datalab-cn-redshift-prd-cn-north-1-role"
        AWS_REGION="cn-north-1"
    fi

    cat <<EOF
ENV=$ENV
JWT_SECRET=$API_KEY
API_KEY=$API_KEY
AWS_DATABASE_SECRET=$DATABASE_SECRET
AWS_RDS_DATABASE_SECRET=$RDS_DATABASE_SECRET
AWS_DATABASE_SECRET_REGION=$DB_REGION
AWS_DATABASE_HOST=$DB_HOST
AWS_DATABASE_PORT=$DB_PORT
AWS_AIRFLOW_SECRET=AIRFLOW/keyrotation_service_account
AWS_AIRFLOW_SECRET_REGION=$DB_REGION
AWS_AIRFLOW_ENDPOINT=$AIRFLOW_ENDPOINT
AWS_AIRFLOW_AUTH_ENDPOINT=$AIRFLOW_AUTH_ENDPOINT
AWS_S3_BUCKET=$S3_BUCKET
AWS_REGION=$AWS_REGION
AWS_S3_PREFIX=competitor_app_scripts
REDSHIFT_ROLE_$ENV=$REDSHIFT_ROLE
## for local
AWS_AIRFLOW_USERNAME=admin
AWS_AIRFLOW_PASSWORD=admin
EOF
}

deploy_server() {
    echo "Starting deployment to $ENV server ($SERVER_IP)"

    # Generate .env locally
    create_env_file > "$WORKSPACE/.env"

    # Rsync project (excluding .env)
    RSYNC_CMD="rsync -avz --exclude '.git' --exclude '.jenkinsfile' --exclude '.cicd' --exclude '.gitignore' --exclude 'control.sh' --exclude '.env' -e "
    if [[ -n "$SSH_KEY" ]]; then
        RSYNC_CMD+="'ssh -i $SSH_KEY -o StrictHostKeyChecking=no'"
    else
        RSYNC_CMD+="'ssh -o StrictHostKeyChecking=no'"
    fi
    RSYNC_CMD+=" $WORKSPACE/ competitorapp@$SERVER_IP:/home/competitorapp/source/"
    eval $RSYNC_CMD

    # Rsync .env directly to flask/
    RSYNC_ENV="rsync -avz -e "
    if [[ -n "$SSH_KEY" ]]; then
        RSYNC_ENV+="'ssh -i $SSH_KEY -o StrictHostKeyChecking=no'"
    else
        RSYNC_ENV+="'ssh -o StrictHostKeyChecking=no'"
    fi
    RSYNC_ENV+=" $WORKSPACE/.env competitorapp@$SERVER_IP:/home/competitorapp/source/flask/"
    eval $RSYNC_ENV

    # SSH deploy commands
    SSH_CMD="ssh "
    [[ -n "$SSH_KEY" ]] && SSH_CMD+="-i $SSH_KEY "
    SSH_CMD+="-o StrictHostKeyChecking=no competitorapp@$SERVER_IP"

    $SSH_CMD <<'EOF'

# Backend Service
cd /home/competitorapp/source/flask

# Activate Python virtual environment
source venv/bin/activate

# Restart Flask
pip install -r requirements.txt
sudo systemctl restart flask
systemctl status flask --no-pager

# Frontend Service
cd /home/competitorapp/source/app

# Restart Nextjs
npm install
npm run build
pm2 restart nextjs-app

# Restart Nginx
sudo systemctl restart nginx
systemctl status nginx --no-pager
EOF

    echo "Deployment to $ENV server ($SERVER_IP) completed."

    # Clean up SSH key if used
    [[ -n "$SSH_KEY" ]] && rm -f "$SSH_KEY"
}

# Start deployment
deploy_server

echo "Deployment finished!"