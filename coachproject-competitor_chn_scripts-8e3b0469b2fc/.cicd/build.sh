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

REGION=cn-north-1
if [[ "$BRANCH" == "DEV" ]]; then 
	REGION=ap-southeast-1
fi
