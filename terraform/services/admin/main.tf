variable "region" {}
variable "env" {}
variable "name" {}

variable "vpc_id" {}
variable "vpc_cidr" {}
variable "public_cidr" {}
variable "subnet_ids" {}

variable "ami" {
    default = ""
}
variable "instance_type" {
    default = "t2.micro"
}
variable "key_name" {}

resource "aws_security_group" "admin" {
    name = "${var.name}"
    vpc_id = "${var.vpc_id}"

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    ingress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["${var.public_cidr}"]
    }

    ingress {
        from_port = 443
        to_port = 443
        protocol = "tcp"
        cidr_blocks = ["${var.public_cidr}"]
    }

    ingress {
        from_port = 3000
        to_port = 3000
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    lifecycle {
        create_before_destroy = true
    }
}

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

    vpc_security_group_ids = ["${aws_security_group.admin.id}"]
    subnet_id = "${element(split(",", var.subnet_ids), 0)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${aws_iam_instance_profile.default.name}"

    # FIXME: This is what's used in production.
    # instance_type = "c3.xlarge"
    instance_type = "${var.instance_type}"

    tags {
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}

resource "aws_eip" "admin" {
  instance = "${aws_instance.admin.id}"
  vpc      = true
}
