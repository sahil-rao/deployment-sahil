variable "region" {}
variable "env" {}
variable "name" {}

##############################################################################

variable "vpc_id" {}
variable "subnet_ids" {
    type = "list"
}
variable "dns_zone_id" {}
variable "security_groups" {
    type = "list"
}

##############################################################################

variable "iam_instance_profile" {}

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

##############################################################################

module "bitnami_nodejs" {
    source = "../../modules/bitnami"
    region = "${var.region}"
    distribution = "nodejs-6.2.0-0"
    architecture = "x86_64"
    virttype = "hvm"
}

##############################################################################

resource "aws_instance" "default" {
    # FIXME: This is using this ami in production:
    # bitnami-nodejs-5.2.0-0-linux-ubuntu-14.04.3-x86_64-hvm-ebs (ami-53445832)
    ami = "${coalesce(var.ami, module.bitnami_nodejs.ami_id)}"
    vpc_security_group_ids = ["${var.security_groups}"]
    subnet_id = "${element(var.subnet_ids, count.index)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${var.iam_instance_profile}"

    # FIXME: This is what's used in production.
    # instance_type = "c3.xlarge"
    # count = 2
    instance_type = "${var.instance_type}"
    count = "${var.instance_count}"

    tags {
        Terraform = "managed"
        Cluster = "${var.env}"
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}

###################################################################

resource "aws_route53_record" "default" {
    count = "${var.instance_count}"
    zone_id = "${var.dns_zone_id}"
    name = "nodejs-${count.index}"
    type = "A"
    ttl = "60"
    records = ["${element(aws_instance.default.*.private_ip, count.index)}"]
}
