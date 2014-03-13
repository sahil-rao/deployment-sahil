#!/bin/bash

cd /home/ubuntu/build/deployment

while read line
do
    buildversion=$line
    echo "Current-Build $name"
done < BuildInfo

echo "Deploying Build $buildversion"

cd /home/ubuntu/build/deployment/playbooks/
/usr/local/bin/ansible-playbook site.yml --limit 'tag_Name_Backoffice,tag_Name_NodeJS,' --extra-vars "BuildVersion=$buildversion"
