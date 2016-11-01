variable "region" {}
variable "env" {}
variable "name" {}

###################################################################

variable "vpc_id" {}
variable "subnet_ids" {
    type = "list"
}
variable "dns_zone_id" {}
variable "security_groups" {
    type = "list"
}

###################################################################

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

###################################################################

###################################################################

module "ubuntu" {
    source = "../../modules/tf_aws_ubuntu_ami"
    region = "${var.region}"
    distribution = "trusty"
    virttype = "hvm"
    storagetype = "ebs-ssd"
}

resource "aws_instance" "default" {
    # FIXME: Production uses this AMI, which needs to be copied over to this image.
    # Backoffice-Foundation-07-16-2014 (ami-79b6cf49)
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
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
    zone_id = "${var.dns_zone_id}"
    count = "${var.instance_count}"
    name = "backoffice-${count.index}"
    type = "A"
    ttl = "5"
    records = ["${element(aws_instance.default.*.private_ip, count.index)}"]
}

###################################################################

output "instance_ids" {
    value = ["${aws_instance.default.*.id}"]
}
