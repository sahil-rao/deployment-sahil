Setup

```
% terraform remote config \
  -backend=s3 \
  -backend-config="profile=navopt_stage" \
  -backend-config="bucket=cloudera-terraform-infrastructure" \
  -backend-config="key=stage/navopt-us-west-2-staging/external/terraform.tfstate" \
  -backend-config="region=us-west-2"
% terraform remote pull
...
% terraform remote push
```
