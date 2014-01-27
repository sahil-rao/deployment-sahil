#!/bin/bash
if [ $# -ne 1 ]
then
  echo "Usage: Needs parameter, [tenant name]"
  exit 65
fi
mongo $1 --eval "db.dropDatabase();"
sudo rm -rf /mnt/volume1/compile-$1/
sudo rm -rf /mnt/volume1/$1/

