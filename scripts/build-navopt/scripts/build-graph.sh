#!/bin/bash

set -eux

BRANCH=$1

git -C /gitcache/graph archive $BRANCH | tar -x

echo "--- building graph..."
python setup.py bdist
cp dist/flightpath-1.0.linux-x86_64.tar.gz /target/flightpath-deployment.tar.gz
tar czf /target/regression-deployment.tar.gz test/
