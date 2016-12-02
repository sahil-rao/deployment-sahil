cloudwatch-log-group
====================

Terraform module that creates an AWS CloudWatch Log Group and
optionally subscribes that group to send events to a destination.

## Input variables

 * `name` (required) - The name of the log group
 * `retention_in_days` (optional) - Specifies the number of days you want to
   retain log events in the specified log group.
 * `subscription_filter_pattern` (optional) - A valid CloudWatch Logs filter
   pattern for subscribing to a filtered stream of log events.
 * `subscription_role_arn` (optional) - The ARN of an IAM role
   that grants Amazon CloudWatch Logs permissions to deliver
   ingested log events to the destination stream.
 * `subscription_destination_arn` (optional) - The ARN of the
   destination to deliver matching log events to.

## Outputs

 * `arn` -  The Amazon Resource Name (ARN) specifying the log subscription
   filter.

## Example use

```
module "cloudwatch-log-group" {
    name = "syslogs"
    retention_in_days = 90
}
```
