variable "region" {}
variable "env" {}
variable "name" {}

##############################################################################

variable "vpc_id" {}
variable "subnet_ids" {
    type = "list"
}
variable "public_subnet_ids" {
    type = "list"
}
variable "dns_zone_id" {}
variable "security_groups" {
    type = "list"
}

variable "nodejs_elb_security_groups" {
    type = "list"
}

variable "nodejs_elb_internal" {}

##############################################################################

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

##############################################################################
variable "navopt_elb_cert_arn" {}

variable "elb_access_logs_interval" {
    description = "The publishing interval in minutes."
    default = "60"
}

variable "elb_access_logs_enabled" {
    description = "Boolean to enable / disable access_logs."
    default = "true"
}

##############################################################################
data "aws_region" "current" {
    current = true
}

module "elb_access_logs" {
    source = "../../modules/elb-access-logs"
    region = "${data.aws_region.current.name}"
}

module "bitnami_nodejs" {
    source = "../../modules/bitnami"
    region = "${var.region}"
    distribution = "nodejs-6.2.0-0"
    architecture = "x86_64"
    virttype = "hvm"
}

##############################################################################

resource "aws_instance" "default" {
    # FIXME: This is using this ami in production:
    # bitnami-nodejs-5.2.0-0-linux-ubuntu-14.04.3-x86_64-hvm-ebs (ami-53445832)
    ami = "${coalesce(var.ami, module.bitnami_nodejs.ami_id)}"
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

resource "aws_elb" "default" {
    name = "navopt-elb"
    subnets = ["${var.public_subnet_ids}"]
    security_groups = ["${var.nodejs_elb_security_groups}"]

    access_logs {
      bucket = "${module.elb_access_logs.bucket}"
      interval = "${var.elb_access_logs_interval}"
      enabled = "${var.elb_access_logs_enabled}"
    }
    
    listener {
      instance_port = 3000
      instance_protocol = "http"
      lb_port = 443
      lb_protocol = "https"
      ssl_certificate_id = "${var.navopt_elb_cert_arn}"
    }

    health_check {
      healthy_threshold = 10
      unhealthy_threshold = 2
      timeout = 5
      target = "TCP:3000"
      interval = 30
    }

  
    instances = ["${aws_instance.default.*.id}"]

    connection_draining = true
    connection_draining_timeout = 60
    idle_timeout = 60

    cross_zone_load_balancing = true
    internal = "${var.nodejs_elb_internal}"
}

###################################################################

resource "aws_route53_record" "default" {
    count = "${var.instance_count}"
    zone_id = "${var.dns_zone_id}"
    name = "nodejs-${count.index}"
    type = "A"
    ttl = "60"
    records = ["${element(aws_instance.default.*.private_ip, count.index)}"]
}

output "instance_ids" {
    value = ["${aws_instance.default.*.id}"]
}

