# This module creates all cloudwatch resources

####################
# Required variables
####################

variable "name" {
    description = "The name of the log group"
}

variable "retention_in_days" {
    description = "Specifies the number of days you want to retain log events in the specified log group."
}

variable "subscription_filter_pattern" {
    description = "A valid CloudWatch Logs filter pattern for subscribing to a filtered stream of log events."
    default = ""
}

variable "subscription_role_arn" {
    description = "The ARN of an IAM role that grants Amazon CloudWatch Logs permissions to deliver ingested log events to the destination stream."
    default = ""
}

variable "subscription_destination_arn" {
    description = "The ARN of the destination to deliver matching log events to."
    default = ""
}

###########
# Resources
###########

resource "aws_cloudwatch_log_group" "group" {
    name = "${var.name}"
    retention_in_days = "${var.retention_in_days}"
}

resource "aws_cloudwatch_log_subscription_filter" "subscriptions" {
    name = "${var.name}"

    # Only setup the subscription filter if a destination filter is specified.
    count = "${signum(length(var.subscription_destination_arn))}"

    destination_arn = "${var.subscription_destination_arn}"
    filter_pattern = "${var.subscription_filter_pattern}"
    log_group_name = "${var.name}"
    role_arn = "${var.subscription_role_arn}"
}

#########
# Outputs
#########

output "name" {
    value = "${var.name}"
}

output "arn" {
    value = "${aws_cloudwatch_log_group.group.arn}"
}
