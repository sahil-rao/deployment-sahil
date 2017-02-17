#!/bin/bash

set -euv

# Script to pull salt states
# Intended to be used as part of a cron

curl_check ()
{
    if [ $1 -ne 0 ]
    then
        ${LOG_CMD} "Problems reaching AWS meta-data service"
        ${LOG_CMD} "Aborting pull of Salt states"
        exit 2
    fi
}

error_message ()
{
    ${LOG_CMD} "Problems pulling or applying salt states"
    exit 3
}

(
    # Set lock file
    # derived from http://stackoverflow.com/a/13551882/524568?
    flock -x -w 1 200 || exit 1

    PATH=$PATH:/usr/local/bin:/usr/bin
    export AWS_DEFAULT_REGION='us-west-2'
    S3_BUCKET='cloudera-sre-us-west-2-prod-salt-states'
    LOG_CMD='logger -t salt-cron -i'


    # Check if instance has finished booting
    if [ ! -f /var/lib/cloud/instance/boot-finished ]
    then
        ${LOG_CMD} "Instance has not finished booting"
        exit 3
    fi

    security_group=$(curl http://169.254.169.254/latest/meta-data/security-groups || curl_check "$?")

    # Don't pull salt states if we're in the middle of a packer build
    if [ ${security_group} == 'packer-service' ]
        then
        ${LOG_CMD} "We appear to be in the middle of a Packer Bake"
        ${LOG_CMD} "Aborting pull of Salt states"
        exit 1
    fi

    # Retrieve and apply global salt states
    aws s3 cp s3://${S3_BUCKET}/global/minion /etc/salt/ && \
            aws s3 sync --delete s3://${S3_BUCKET}/global/states/ /srv/salt/ && \
            salt-call --local state.apply || \
            error_message

    ${LOG_CMD} "Applied global salt states"

    ACCOUNT_ID=`curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep -oP '(?<="accountId" : ")[^"]*(?=")'`

    project='navopt'
    case $ACCOUNT_ID in
      128669107540) profile='dev';;
      001209911431) profile='stage';;
      892272719698) profile='prod';;
      *)
        ${LOG_CMD} "Unable to determing which environment this is, exiting"
        exit 4
        ;;
    esac

    if [ -z ${profile} ] || [ -z ${project} ]
    then
        ${LOG_CMD} "Unable to determing which environment this is"
        exit 4
    fi

    # Pull salt states specific to this project
    aws s3 sync s3://${S3_BUCKET}/accounts/${project}-${profile}/ /srv/salt/ && \
        salt-call --local state.apply || \
        error_message

    ${LOG_CMD} "Retrieved and applied salt states for ${project}-${profile}"

) 200>/var/lock/salt_cron.lock
