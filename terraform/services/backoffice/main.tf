variable "region" {}
variable "env" {}
variable "name" {}

variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}

variable "iam_role_name" { default = "" }
variable "iam_role_policy_name" { default = "" }
variable "iam_instance_profile" { default = "" }

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

module "bitnami_nodejs" {
    source = "../../modules/bitnami"
    region = "${var.region}"
    distribution = "nodejs-6.2.0-0"
    architecture = "x86_64"
    virttype = "hvm"
}

resource "aws_security_group" "default" {
    name = "${var.name}"
    vpc_id = "${var.vpc_id}"

    ingress {
        from_port = 26379
        to_port = 26379
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    ingress {
        from_port = 6379
        to_port = 6379
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    # FIXME: why?
    ingress {
        from_port = 7432
        to_port = 7432
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    # FIXME: why?
    ingress {
        from_port = 7180
        to_port = 7183
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    # FIXME: why?
    ingress {
        from_port = 5601
        to_port = 5601
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    # FIXME: why?
    ingress {
        from_port = 9300
        to_port = 9300
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidr}"]
    }

    # FIXME: why?
    ingress {
        from_port = 9200
        to_port = 9200
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

resource "aws_instance" "default" {
    # FIXME: Production uses this AMI, which needs to be copied over to this image.
    # Backoffice-Foundation-07-16-2014 (ami-79b6cf49)
    ami = "${coalesce(var.ami, module.bitnami_nodejs.ami_id)}"
    vpc_security_group_ids = ["${aws_security_group.default.id}"]
    subnet_id = "${element(split(",", var.subnet_ids), 0)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${aws_iam_instance_profile.default.name}"

    # FIXME: This is what's used in production.
    # instance_type = "c3.xlarge"
    # count = 2
    instance_type = "${var.instance_type}"
    count = "${var.instance_count}"

    tags {
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}
