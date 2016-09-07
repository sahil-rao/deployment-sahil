#!/bin/bash

set -eux

BRANCH=$1

git -C /gitcache/analytics archive $BRANCH | tar -x

echo "--- building analytics..."
python setup.py bdist
cd dist
cp baazmath-1.0.linux-x86_64.tar.gz /target/Baaz-Analytics.tar.gz
