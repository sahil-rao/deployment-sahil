Setup

```
% terraform remote config \
  -backend=s3 \
  -backend-config="profile=navopt_dev" \
  -backend-config="bucket=cloudera-terraform-infrastructure" \
  -backend-config="key=dev/navopt-us-west-2-dev/external/terraform.tfstate" \
  -backend-config="region=us-west-2"
% terraform remote pull
...
% terraform remote push
```
