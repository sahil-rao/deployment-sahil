variable "account_id" {
    default = "001209911431"
}

variable "region" {
    default = "us-west-2"
}

variable "vpc_name" {
    default = "navopt-stage"
}

variable "vpc_cidr" {
   default = "10.7.0.0/17"
}

variable "availability_zones" {
    default = "us-west-2a,us-west-2b,us-west-2c"
}

variable "public_subnets" {
    default = "10.7.0.0/21,10.7.8.0/21,10.7.16.0/21"
}

variable "public_subnets_count" {
    default = 3
}

variable "private_subnets" {
    default = "10.7.24.0/21,10.7.32.0/21,10.7.40.0/21"
}

variable "private_subnets_count" {
    default = 3
}

variable "virtual_gateway_id" {
    default = "vgw-b4e63faa"
}
