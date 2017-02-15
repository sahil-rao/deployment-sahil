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
