module "redis-lc" {
    source = "../redis-lc"

    name_prefix = "${var.name}-${var.version}-"

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.iam_instance_profile}"

    zone_name = "${var.zone_name}"
    security_groups = "${var.security_groups}"

    ami_id = "${var.ami_id}"
    instance_type = "${var.instance_type}"
    ebs_optimized = "${var.ebs_optimized}"
    quorum_size = "${var.quorum_size}"
    backups_enabled = "${var.backups_enabled}"

    env = "${var.env}"
    service = "${var.service}"
    datadog_api_key = "${var.datadog_api_key}"
}

module "redis-asg" {
    source = "../redis-asg"

    name = "${var.name}"
    version = "${var.version}"
    launch_configuration = "${module.redis-lc.name}"
    subnet_ids = "${var.subnet_ids}"

    env = "${var.env}"
    service = "${var.service}"

    min_size = "${var.min_size}"
    max_size = "${var.max_size}"
    desired_capacity = "${var.desired_capacity}"
}

/*
variable "region" {}
variable "env" {}
variable "name" {}

###################################################################

variable "vpc_id" {}
variable "vpc_cidr" {}
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
    # FIXME: Production uses this AMI, which needs to be copied over to this image.
    # Redis v11 (ami-ee16f98e)
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
    vpc_security_group_ids = ["${var.security_groups}"]
    subnet_id = "${element(var.subnet_ids, count.index)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${var.iam_instance_profile}"

    # FIXME: This is what's used in production.
    # instance_type = "r3.2xlarge"
    # count = 3
    instance_type = "${var.instance_type}"
    count = "${var.instance_count}"
    ebs_optimized = "${var.ebs_optimized}"

    tags {
        Cluster = "${var.env}"
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}

###################################################################

resource "aws_route53_record" "default" {
    zone_id = "${var.dns_zone_id}"
    count = "${var.instance_count}"
    name = "${var.name}-${count.index}"
    type = "A"
    ttl = "5"
    records = ["${element(aws_instance.default.*.private_ip, count.index)}"]
}
*/
