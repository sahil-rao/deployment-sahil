#!/bin/bash

set -eux

BRANCH=$1

git -C /gitcache/UI archive $BRANCH | tar -x

echo "--- building UI..."
cd webapp/war
tar -zcf /target/UI.tar.gz *
cd ../..

tar -zcf /target/xplain.io.tar.gz xplain.io
tar -zcf /target/optimizer_api.io.tar.gz optimizer_api
tar -zcf /target/xplain_dashboard.tar.gz xplain_dashboard
tar -zcf /target/optimizer_admin.io.tar.gz optimizer_admin
