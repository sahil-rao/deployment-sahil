variable "name" {}
variable "version" {}

variable "vpc_id" {}
variable "subnet_ids" {
    type = "list"
}

variable "key_name" {}
variable "instance_type" {}
variable "min_size" {}
variable "max_size" {}
variable "desired_capacity" {}
