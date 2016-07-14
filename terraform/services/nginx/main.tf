variable "env" {}
variable "name" {}

###################################################################

variable "region" {}
variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}
variable "public_cidr" {}

###################################################################

variable "security_group_name" {
    default = ""
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
variable "iam_instance_profile" {
    default = ""
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

resource "aws_security_group" "default" {
    name = "${coalesce(var.security_group_name, var.name)}"
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

resource "aws_instance" "default" {
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
    vpc_security_group_ids = ["${aws_security_group.default.id}"]
    subnet_id = "${element(split(",", var.subnet_ids), 0)}"
    key_name = "${var.key_name}"

    # FIXME: Does this need an IAM role?
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
