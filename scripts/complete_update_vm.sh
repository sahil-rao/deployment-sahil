#!/bin/bash
cd ~/build/deployment
git checkout .
git checkout master
git pull
cp scripts/update-vm.sh ~/.
cd
./update-vm.sh $1
