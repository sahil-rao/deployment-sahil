variable "region" {}
variable "env" {}
variable "name" {}

###################################################################

variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}
variable "public_cidr" {}
variable "dns_zone_id" {}
variable "security_groups" {}
variable "iam_instance_profile" {}

###################################################################

variable "ami" {
    default = ""
}
variable "instance_type" {
    default = "t2.micro"
}
variable "key_name" {}

###################################################################

module "bitnami_nodejs" {
    source = "../../modules/bitnami"
    region = "${var.region}"
    distribution = "nodejs-6.2.0-0"
    architecture = "x86_64"
    virttype = "hvm"
}

resource "aws_instance" "admin" {
    # FIXME: This is using this ami in production:
    # bitnami-nodejs-4.4.4-0-linux-ubuntu-14.04.3-x86_64-hvm-ebs (ami-5b85783b)
    ami = "${coalesce(var.ami, module.bitnami_nodejs.ami_id)}"

    vpc_security_group_ids = ["${split(",", var.security_groups)}"]
    subnet_id = "${element(split(",", var.subnet_ids), 0)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${var.iam_instance_profile}"

    # FIXME: This is what's used in production.
    # instance_type = "c3.xlarge"
    instance_type = "${var.instance_type}"

    tags {
        Terraform = "managed"
        Cluster = "${var.env}"
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}

resource "aws_eip" "admin" {
  instance = "${aws_instance.admin.id}"
  vpc      = true
}

###################################################################

resource "aws_route53_record" "admin" {
    zone_id = "${var.dns_zone_id}"
    name = "admin"
    type = "A"
    ttl = "5"
    records = ["${aws_instance.admin.private_ip}"]
}
