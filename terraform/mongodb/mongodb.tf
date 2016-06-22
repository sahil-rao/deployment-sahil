provider "aws" {
    profile = "navopt_prod"
    region = "us-west-1"
}

variable "subnet_ids" {
    default = "subnet-6caca20e,subnet-82145ec4"
}

variable "security_groups" {
    default = "sg-acd8d1ce"
}

variable "dbsilo" {
    default = "dbsilo4"
}

variable "cluster" {
    default = "alpha"
}

module "blue" {
    source = "./blue-green"

    blue_green = "blue"
    ami_id = "ami-50400430"
    subnet_ids = "${var.subnet_ids}"
    security_groups = "${var.security_groups}"

    dbsilo = "${var.dbsilo}"
    cluster = "${var.cluster}"

    min_size = 3
    max_size = 3
    desired_capacity = 3
}

/*
module "green" {
    source = "./blue-green"

    blue_green = "green"
    ami_id = "ami-50400430"
    subnet_ids = "${var.subnet_ids}"
    security_groups = "${var.security_groups}"

    dbsilo = "${var.dbsilo}"
    cluster = "${var.cluster}"

    min_size = 3
    max_size = 3
    desired_capacity = 3
}
*/
