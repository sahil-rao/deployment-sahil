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

###################################################################

variable "iam_instance_profile" {}

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
variable "ebs_optimized" {
    default = "false"
}

###################################################################

module "ubuntu" {
    source = "../../modules/tf_aws_ubuntu_ami"
    region = "${var.region}"
    distribution = "trusty"
    virttype = "hvm"
    storagetype = "ebs-ssd"
}

###################################################################

resource "aws_instance" "default" {
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
    vpc_security_group_ids = ["${split(",", var.security_groups)}"]
    subnet_id = "${element(split(",", var.subnet_ids), 0)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${var.iam_instance_profile}"

    # FIXME: This is what's used in production.
    # instance_type = "m4.xlarge"
    instance_type = "${var.instance_type}"
    ebs_optimized = "${var.ebs_optimized}"

    tags {
        Cluster = "${var.env}"
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}

resource "aws_eip" "default" {
  instance = "${aws_instance.default.id}"
  vpc      = true
}

###################################################################

resource "aws_route53_record" "default" {
    zone_id = "${var.dns_zone_id}"
    count = "${var.instance_count}"
    name = "lb-${count.index}"
    type = "A"
    ttl = "5"
    records = ["${element(aws_instance.default.*.private_ip, count.index)}"]
}
