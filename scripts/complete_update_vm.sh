#!/bin/bash
cd ~/build/deployment
git checkout .
git checkout master
git pull
cp ./scripts/update-vm.sh ~/.
cp ./scripts/gulpfile.js ~/.
cp ./scripts/package.json ~/.
cd
./update-vm.sh $1
