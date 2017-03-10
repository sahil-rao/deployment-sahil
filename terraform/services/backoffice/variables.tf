variable "region" {}
variable "env" {}
variable "name" {}

variable "sg_name" {}
variable "iam_role_name" {}

###################################################################

variable "vpc_id" {}
variable "private_cidrs" {
    type = "list"
}
variable "subnet_ids" {
    type = "list"
}
variable "dns_zone_id" {}

###################################################################

variable "ami" {
    default = ""
}
variable "instance_type" {
    default = "t2.micro"
}
variable "instance_count" {
    default = 1
}
variable "key_name" {}

###################################################################

variable "cloudwatch_retention_in_days" {}
variable "log_subscription_destination_arn" {}

variable "s3_navopt_bucket_arn" {}
