variable "vpc_id" {}
variable "private_cidrs" {
    type = "list"
}
variable "subnet_ids" {
    type = "list"
}
variable "zone_id" {}
variable "zone_name" {}

###################################################################

variable "name" {}
variable "version" {}
variable "service" {}
variable "env" {}
variable "datadog_api_key" {}

###################################################################

variable "key_name" {}

###################################################################

variable "ami_id" {}
variable "instance_type" {}
variable "min_size" {}
variable "max_size" {}
variable "desired_capacity" {}
variable "ebs_optimized" {
    default = true
}

variable "cloudwatch_retention_in_days" {}
variable "log_subscription_destination_arn" {}

variable "elasticsearch_heap_size" {}
