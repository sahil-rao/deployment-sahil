log-service
===========

Terraform module that specifies the SRE Log Service Destination ARNs.


## Input variables

 * `environment` (required) - The type of environment: prod/staging/dev/etc

## Outputs

 * `destination_arn` - The Amazon Resource Name (ARN) specifying the log
   destination.

## Example use

```
module "log-service" {
    source = "../../modules/log-service"
    environment = dev"
}

module "cloudwatch-log-group" {
    source = "../../modules/cloudwatch-log-group"

    name = "syslog"
    subscription_destination_arn = "${module.log-service.destination_arn}"
}
```
