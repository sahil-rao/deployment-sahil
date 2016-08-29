Setup

```
% terraform remote config \
  -backend=s3 \
  -backend-config="profile=navopt_dev" \
  -backend-config="bucket=navopt-state-dev" \
  -backend-config="key=us-west-2/terraform.tfstate" \
  -backend-config="region=us-west-2"
% terraform remote pull
...
% terraform remote push
```
