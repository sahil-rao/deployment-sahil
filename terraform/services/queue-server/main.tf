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

variable "iam_role_name" { default = "queue_server" }
variable "instance_managed_policies" { type = "list" }
variable "num_instance_managed_policies" {}

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

variable "cloudwatch_retention_in_days" {}
variable "log_subscription_destination_arn" {}

###################################################################

module "ubuntu" {
    source = "../../modules/tf_aws_ubuntu_ami"
    region = "${var.region}"
    distribution = "trusty"
    virttype = "hvm"
    storagetype = "ebs-ssd"
}

###################################################################

module "queue-server-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "${var.name}"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

###################################################################

resource "aws_instance" "default" {
    # FIXME: this uses this ami in production:
    # Xplain-RabbitMQ-3.3.4/Erlang17_Version1 (ami-3fe79e0f)
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
    vpc_security_group_ids = ["${var.security_groups}"]
    subnet_id = "${element(var.subnet_ids, count.index)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${aws_iam_instance_profile.queue_server.name}"

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

###################################################################

resource "aws_route53_record" "default" {
    zone_id = "${var.dns_zone_id}"
    count = "${var.instance_count}"
    name = "queue-${count.index}"
    type = "A"
    ttl = "5"
    records = ["${element(aws_instance.default.*.private_ip, count.index)}"]
}
