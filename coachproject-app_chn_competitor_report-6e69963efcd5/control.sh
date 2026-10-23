#!/bin/bash
#checkrsync
source ${HOME}/.config/control_variables.conf

HOME_DIR=${HOME}/jobs/$PROJECT/$REPO
DATE=$(date +"%F %T")

mkdir -p ${HOME_DIR}/logs 2>/dev/null
function log {
LOGDATE=$(date +"%Y-%m-%d %T,%s")
if [[ $1 == 0 ]]; then
    echo -e "[$LOGDATE] INFO - Completed Step: $2" >> ${HOME_DIR}/logs/$REPO.log
else
    echo -e "[$LOGDATE] ERROR - Failed on Step: $2" >> ${HOME_DIR}/logs/$REPO.err
    exit 1;
fi
}

while (( "$#" ));
do
    if [ $1 == "-s1" ] || [ $1 == "--sample-parameter" ] ; then
        SAMPLEPARAM1=$2
    elif [ $1 == "-s2" ] || [ $1 == "--sample-parameter2" ] ; then
        SAMPLEPARAM2="SAMPLEVALUESET"
    fi
shift
done

##SAMPLE: Parameter Validation
if [[ -z $SAMPLEPARAM1 ]]; then
    echo "PARAM1 must be set"
    exit 1;
fi

#SAMPLE: Set Array to Default List
if [[ ! -z $SAMPLEPARAM2 ]]; then
         INTERFACES=( interface1 interface2 )
fi


####################################
##     Start Code Calls Below     ##
####################################

##DELETE/Modify Below

#Sample Loop Though List
for ((i=0; i<${#INTERFACES[*]}; i++));
do
        echo "${INTERFACES[i]^^}"
        log $? "Echoing ${INTERFACES[i]}"
done

#Sample execute snowsql script
snowsql -f ${HOME_DIR}/scripts/file.sql
log $? "Desc of file.sql"

#Sample execute Python code
python3 ${HOME_DIR}/scripts/sample.py
log $? "Sample python script"
