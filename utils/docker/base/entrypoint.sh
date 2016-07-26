#!/bin/sh

set -e

MICROSERVICE_NAME=`ls /*env | awk -F'.' '{ print $1 }' | awk -F'/' '{ print $2 }'`

setup_prod(){
    echo "prod"
}

LAUNCH_SHELL=no

for arg in $@
do
    if [ "$arg" = "dev" ]
    then
        . /$MICROSERVICE_NAME.env
    elif [ "$arg" = "shell" ]
    then
        LAUNCH_SHELL=yes
    elif [ "$arg" = "prod" ]
    then
        setup_prod
    fi
done

if [ "$LAUNCH_SHELL" = "yes" ]
then
    exec /bin/bash
else
    exec /usr/local/bin/supervisord -n

fi
