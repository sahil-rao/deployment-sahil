# NavOpt Build Script

`build-navopt` builds the NavOpt environment for deployment. It has many
options to make it applicable to deploy the dev, stage, or production versions
of the application. This script has many options, to see them all run
`./build-navopt --help`.

Here's how to see it in action:

```
% ./build-navopt --env dev --dry-run
--- updating git@github.com:baazdata/graph.git
--- updating git@github.com:baazdata/documentation.git
--- updating git@github.com:baazdata/analytics.git
--- updating git@github.com:baazdata/UI.git
--- updating git@github.com:baazdata/deployment.git
--- updating git@github.com:baazdata/compiler.git

------------------------------------------------------------------------------

Are you sure you want to upload the following services? UI analytics compiler deployment documentation graph
[yes/no]: yes
--- uploading target/flightpath-deployment.tar.gz to s3://baaz-deployment/erickt/master/flightpath-deployment.tar.gz
--- uploading documentation/NavOptHelp/ to s3://xplain-public/navopt-dev/documentation/NavOptHelp/
--- uploading target/Baaz-Analytics.tar.gz to s3://baaz-deployment/erickt/master/Baaz-Analytics.tar.gz
--- uploading target/xplain.io.tar.gz to s3://baaz-deployment/erickt/master/xplain.io.tar.gz
--- uploading target/optimizer_api.io.tar.gz to s3://baaz-deployment/erickt/master/optimizer_api.io.tar.gz
--- uploading target/xplain_dashboard.tar.gz to s3://baaz-deployment/erickt/master/xplain_dashboard.tar.gz
--- uploading target/optimizer_admin.io.tar.gz to s3://baaz-deployment/erickt/master/optimizer_admin.io.tar.gz
--- uploading target/Baaz-DataAcquisition-Service.tar.gz to s3://baaz-deployment/erickt/master/Baaz-DataAcquisition-Service.tar.gz
--- uploading target/Baaz-Compile-Service.tar.gz to s3://baaz-deployment/erickt/master/Baaz-Compile-Service.tar.gz
--- uploading target/Baaz-Analytics-Service.tar.gz to s3://baaz-deployment/erickt/master/Baaz-Analytics-Service.tar.gz
--- uploading target/Baaz-Compiler.tar.gz to s3://baaz-deployment/erickt/master/Baaz-Compiler.tar.gz
```

Notice that `[yes/no]:` prompt? It confirms with you first before you upload
packages.  To actually see the commands it will run, just run it with verbosity
(and we'll pass `--yes` to assume yes):

```
% ./build-navopt --env dev --dry-run -v --yes
--- updating git@github.com:baazdata/graph.git
+ git -C .gitcache/graph remote set-url origin git@github.com:baazdata/graph.git
+ git -C .gitcache/graph remote update origin
+ docker build -t build-navopt scripts
+ docker run -v /Users/erickt/.m2:/root/.m2 -v /Users/erickt/projects/cloud/navopt/deployment/scripts/build-navopt/.gitcache:/gitcache -v /Users/erickt/projects/cloud/navopt/deployment/scripts/build-navopt/target:/target -v /Users/erickt/projects/cloud/navopt/deployment/scripts/build-navopt/scripts:/scripts -t build-navopt /scripts/build-graph.sh master
--- updating git@github.com:baazdata/documentation.git
+ git -C .gitcache/documentation remote set-url origin git@github.com:baazdata/documentation.git
+ git -C .gitcache/documentation remote update origin
+ git -C gitcache/documentation archive master NavOptHelp | tar -x -C target
--- updating git@github.com:baazdata/analytics.git
...
```

## Build and Upload a Service

Now that we got that out of the way lets do a real build of just one service, and upload it to
`s3://baaz-development/$USER/master`:

```
--- updating git@github.com:baazdata/UI.git
Fetching origin
--- building UI
...

------------------------------------------------------------------------------

Are you sure you want to upload the following services? UI
[yes/no]: yes
--- uploading target/xplain.io.tar.gz to s3://baaz-deployment/erickt/master/xplain.io.tar.gz
upload: target/xplain.io.tar.gz to s3://baaz-deployment/erickt/master/xplain.io.tar.gz
--- uploading target/optimizer_api.io.tar.gz to s3://baaz-deployment/erickt/master/optimizer_api.io.tar.gz
upload: target/optimizer_api.io.tar.gz to s3://baaz-deployment/erickt/master/optimizer_api.io.tar.gz
--- uploading target/xplain_dashboard.tar.gz to s3://baaz-deployment/erickt/master/xplain_dashboard.tar.gz
upload: target/xplain_dashboard.tar.gz to s3://baaz-deployment/erickt/master/xplain_dashboard.tar.gz
--- uploading target/optimizer_admin.io.tar.gz to s3://baaz-deployment/erickt/master/optimizer_admin.io.tar.gz
upload: target/optimizer_admin.io.tar.gz to s3://baaz-deployment/erickt/master/optimizer_admin.io.tar.gz
```

## Building a Release

This is just like before, but instead we also specify the `--release` flag:

```
% ./build-navopt --env dev --release -v
...
```
