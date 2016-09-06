variable "region" {}
variable "env" {}
variable "name" {}

###################################################################

variable "vpc_id" {}
variable "subnet_ids" {
    type = "list"
}
variable "dns_zone_id" {}

###################################################################

variable "security_groups" {
    type = "list"
}

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
variable "iam_instance_profile" {
    default = ""
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
    # FIXME: uses this ami in production:
    # Deployment-Root (ami-c1d5a5f1)
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
    vpc_security_group_ids = ["${var.security_groups}"]
    subnet_id = "${element(var.subnet_ids, count.index)}"
    key_name = "${var.key_name}"

    # FIXME: Should this have an IAM role?
    # iam_instance_profile = ""

    # FIXME: This is what's used in production.
    # instance_type = "m1.small"
    # count = 3
    instance_type = "${var.instance_type}"
    count = "${var.instance_count}"

    tags {
        Terraform = "managed"
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

resource "aws_route53_record" "bastion" {
    zone_id = "${var.dns_zone_id}"
    name = "deployment-root"
    type = "A"
    ttl = "5"
    records = ["${aws_instance.default.private_ip}"]
}

###################################################################

output "eip" {
    value = "${aws_eip.default.public_ip}"
}
