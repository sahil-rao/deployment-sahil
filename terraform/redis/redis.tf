variable "subnet_ids" {}
variable "security_groups" {}

variable "name_prefix" {}
variable "dbsilo_name" {}
variable "cluster_name" {}
variable "datadog_api_key" {}

variable "key_name" {}
variable "instance_profile" {}

variable "ami_id" {}
variable "instance_type" {}
variable "min_size" {}
variable "max_size" {}
variable "desired_capacity" {}

resource "template_file" "user_data" {
    template = "${file("${path.module}/user-data.sh")}"

    vars {
        dbsilo = "${var.dbsilo_name}"
        service = "redis"
        cluster = "${var.cluster_name}"
        datadog_api_key = "${var.datadog_api_key}"
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
    iam_instance_profile = "${var.instance_profile}"
    ebs_optimized = true
    enable_monitoring = false
    key_name = "${var.key_name}"
    security_groups = ["${split(",", var.security_groups)}"]
    user_data = "${template_file.user_data.rendered}"

    root_block_device {
        volume_size = 60
    }

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_autoscaling_group" "default" {
    name = "${aws_launch_configuration.default.name}"

    launch_configuration = "${aws_launch_configuration.default.name}"
    min_size = "${var.min_size}"
    max_size = "${var.max_size}"
    desired_capacity = "${var.desired_capacity}"
    vpc_zone_identifier = ["${split(",", var.subnet_ids)}"]

    tag {
        key = "Name"
        value = "${var.name_prefix}"
        propagate_at_launch = true
    }

    lifecycle {
        create_before_destroy = true
    }
}
