variable "env" {}
variable "name" {}

###################################################################

variable "region" {}
variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}

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

    # Port mapper daemon
    ingress {
        from_port = 4369
        to_port = 4370
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    ingress {
        from_port = 5672
        to_port = 5672
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    # management port
    ingress {
        from_port = 15672
        to_port = 15672
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    ingress {
        from_port = 25672
        to_port = 25672
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    ingress {
        from_port = 35197
        to_port = 35197
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

    tags {
        Terraform = "managed"
    }
}

###################################################################

resource "aws_instance" "default" {
    # FIXME: this uses this ami in production:
    # Xplain-RabbitMQ-3.3.4/Erlang17_Version1 (ami-3fe79e0f)
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
    vpc_security_group_ids = ["${aws_security_group.default.id}"]
    subnet_id = "${element(split(",", var.subnet_ids), 0)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${aws_iam_instance_profile.default.name}"

    # instance_type = "c3.2xlarge"
    # count = 2
    instance_type = "${var.instance_type}"
    count = "${var.instance_count}"
    ebs_optimized = "${var.ebs_optimized}"

    tags {
        Terraform = "managed"
        Cluster = "${var.env}"
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}
