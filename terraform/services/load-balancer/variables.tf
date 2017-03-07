variable "vpc_id" {}
variable "private_cidrs" {
    type = "list"
}
variable "public_cidrs" {
    type = "list"
}
variable "subnet_ids" {
    type = "list"
}

variable "region" {}
variable "env" {}
variable "name" {}

###################################################################

variable "instance_managed_policies" { type = "list" }

# FIXME: This might not be needed in Terraform 0.9.x
variable "num_instance_managed_policies" {}

variable "instance_type" {
    default = "t2.micro"
}
variable "instance_count" {
    default = 1
}
variable "key_name" {}
variable "ebs_optimized" {
    default = "false"
}
