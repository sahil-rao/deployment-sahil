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
variable "backup_file" {
    default = ""
}


variable "quorum_size" {}
variable "backups_enabled" {
    default = false
}

variable "cloudwatch_retention_in_days" {}
variable "log_subscription_destination_arn" {}
