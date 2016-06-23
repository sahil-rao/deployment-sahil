variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}

variable "name_prefix" {}
variable "dbsilo_name" {}
variable "cluster_name" {}

variable "key_name" {}

variable "ami_id" {}
variable "instance_type" {}
variable "min_size" {}
variable "max_size" {}
variable "desired_capacity" {}

resource "aws_security_group" "default" {
    name = "${var.name_prefix}"
    vpc_id = "${var.vpc_id}"

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

    ingress {
        from_port = 26379
        to_port = 26379
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

resource "template_file" "user_data" {
    template = "${file("${path.module}/user-data.sh")}"

    vars {
        dbsilo = "${var.dbsilo_name}"
        service = "redis"
        cluster = "${var.cluster_name}"
        datadog_api_key = "42bbac658841fd4c44253c01423b3227"
        backup_file = "s3://xplain-alpha/redis-backups/${var.cluster_name}-dump.rdb"
    }

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_launch_configuration" "default" {
    name_prefix = "${var.name_prefix}-"
    image_id = "${var.ami_id}"
    instance_type = "${var.instance_type}"
    iam_instance_profile = "${aws_iam_instance_profile.default.name}"
    ebs_optimized = true
    enable_monitoring = false
    key_name = "${var.key_name}"
    security_groups = ["${aws_security_group.default.id}"]
    user_data = "${template_file.user_data.rendered}"

    root_block_device {
        volume_size = 60
    }

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_autoscaling_group" "default" {
    name = "${var.name_prefix}"

    launch_configuration = "${aws_launch_configuration.default.name}"
    min_size = "${var.min_size}"
    max_size = "${var.max_size}"
    desired_capacity = "${var.desired_capacity}"
    vpc_zone_identifier = ["${split(",", var.subnet_ids)}"]
}