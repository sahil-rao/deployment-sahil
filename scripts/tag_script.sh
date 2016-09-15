#!/bin/bash

BRANCH_NAME="master"
TAG_NAME="tmp"
CUR_LOC=$(pwd)

#check what's passed in.
if [ -z "$1" ]
then
  echo "No branch supplied, using master"
else
  BRANCH_NAME=$1
fi

if [ -z "$2" ]
then
  echo "No tag supplied, using tmp"
else
  TAG_NAME=$2
fi

TIME=$(date +"%T")

#pulling all repos and tagging on the specified tag and branch name.
array=("deployment" "analytics" "compiler" "UI" "graph" "documentation")
for REPO in "${array[@]}"
do
    :
    echo $REPO
    if cd $CUR_LOC/$REPO
    then
        git pull
        git checkout $BRANCH_NAME
        git reset --hard
        git pull
        git tag -a $TAG_NAME -m "$TAG_NAME Tag Cut by tag_script.sh at $TIME."
        git push origin $TAG_NAME
        git checkout master
        git pull
    else "$REPO not present."
    fi
done