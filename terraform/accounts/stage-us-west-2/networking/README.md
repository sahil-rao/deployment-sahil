Setup

```
% terraform remote config \
  -backend=s3 \
  -backend-config="profile=navopt_stage" \
  -backend-config="bucket=navopt-state-stage" \
  -backend-config="key=us-west-2/network/terraform.tfstate" \
  -backend-config="region=us-west-2"
% terraform remote pull
...
% terraform remote push
```
