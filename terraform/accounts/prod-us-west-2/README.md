Setup

```
% terraform remote config \
  -backend=s3 \
  -backend-config="profile=navopt_prod" \
  -backend-config="bucket=cloudera-terraform-infrastructure" \
  -backend-config="key=prod/navopt-us-west-2-prod/external/terraform.tfstate" \
  -backend-config="region=us-west-2"
% terraform remote pull
...
% terraform remote push
```
