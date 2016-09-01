variable "env" {}
variable "name" {}

##############################################################################

variable "region" {}
variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}
variable "dns_zone_id" {}

##############################################################################

variable "key_name" {}
variable "security_groups" {
    default = ""
}
variable "ami" {
    default = ""
}
variable "instance_type" {
    default = "t2.micro"
}
variable "instance_count" {
    default = 1
}
variable "iam_instance_profile" {
    default = ""
}
variable "ebs_optimized" {
    default = "false"
}

##############################################################################

module "ubuntu" {
    source = "../../modules/tf_aws_ubuntu_ami"
    region = "${var.region}"
    distribution = "trusty"
    virttype = "hvm"
    storagetype = "ebs-ssd"
}

##############################################################################

resource "aws_instance" "logstash" {
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
    vpc_security_group_ids = ["${split(",", var.security_groups)}"]
    subnet_id = "${element(split(",", var.subnet_ids), 0)}"
    key_name = "${var.key_name}"

    # FIXME: Does this need an IAM role?
    iam_instance_profile = "${var.iam_instance_profile}"

    # FIXME: This is what's used in production.
    # instance_type = "c3.xlarge"
    instance_type = "${var.instance_type}"
    count = "${var.instance_count}"
    ebs_optimized = "${var.ebs_optimized}"

    tags {
        Cluster = "${var.env}"
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}
