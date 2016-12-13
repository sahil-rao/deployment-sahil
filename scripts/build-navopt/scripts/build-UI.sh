#!/bin/bash

set -eux

BRANCH=$1

mkdir UI && git -C /gitcache/UI archive $BRANCH | tar -x -C UI

mkdir deployment
git -C /gitcache/deployment archive $BRANCH | tar -x -C deployment
cp deployment/scripts/gulp-config.js ./
cp deployment/scripts/gulpfile.js ./
cp deployment/scripts/package.json ./
ln -s /usr/bin/nodejs /usr/bin/node
ln -s /node_modules ./node_modules
npm install
gulp app-build


echo "--- building UI..."
cp xplain.io.tar.gz /target/.
tar -zcf /target/optimizer_api.io.tar.gz ./UI/optimizer_api
tar -zcf /target/xplain_dashboard.tar.gz ./UI/xplain_dashboard
tar -zcf /target/optimizer_admin.io.tar.gz ./UI/optimizer_admin
