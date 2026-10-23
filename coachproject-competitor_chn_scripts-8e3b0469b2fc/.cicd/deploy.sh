#!/bin/bash
while (( "$#" ));
do
    if [ "$1" == "-b" ] || [ "$1" == "--branch" ] ; then
        BRANCH=$2
    elif [ "$1" == "-r" ] || [ "$1" == "--repo" ] ; then
        REPO=$2
    elif [ "$1" == "-e" ] || [ "$1" == "--email-list" ] ; then
        ADDITIONAL_EMAILS="-e $2"
    fi
shift
done

if [[ -z $BRANCH ]]; then
	echo "Branch (-b) not set"
	exit 1;
fi

if [[ "$BRANCH" == "master" ]]; then 
		ACCOUNT=175814205108
		REGION="cn-north-1"
        env="prd"
elif [[ $BRANCH == "QA" ]]; then
        ACCOUNT=175826060701
		REGION="cn-north-1"
        env="qa"
elif [[ $BRANCH == "DEV" ]]; then
		ACCOUNT=334242416958
		REGION="ap-southeast-1"
        env="dev"
else
    echo "Error: Unsupported branch $BRANCH"
    exit 1
fi

S3BUCKET=${ACCOUNT}-eds-${env}-${REGION}

# Upload scripts to S3
aws s3 sync $WORKSPACE/python_scripts s3://${S3BUCKET}/competitor_app_scripts/python_scripts/ --region ${REGION}
aws s3 sync $WORKSPACE/sql_scripts s3://${S3BUCKET}/competitor_app_scripts/sql_scripts/ --region ${REGION}
aws s3 sync $WORKSPACE/staging s3://${S3BUCKET}/competitor_app_scripts/staging/ --region ${REGION}

# Check if the upload was successful (exit code 0)
if [ $? -eq 0 ]; then
    echo "Upload successful."
else
    echo "Upload failed."
fi