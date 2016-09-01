variable "subnet_ids" {}
variable "security_groups" {}

###################################################################

variable "name" {}
variable "version" {}
variable "dbsilo_name" {}
variable "cluster_name" {}
variable "datadog_api_key" {}
variable "backup_file" {}

###################################################################

variable "key_name" {}
variable "iam_instance_profile" {}

###################################################################

variable "ami_id" {}
variable "instance_type" {}
variable "min_size" {}
variable "max_size" {}
variable "desired_capacity" {}
variable "ebs_optimized" {
    default = true
}

###################################################################

resource "template_file" "user_data" {
    template = "${file("${path.module}/user-data.sh")}"

    vars {
        dbsilo = "${var.dbsilo_name}"
        service = "redis"
        cluster = "${var.cluster_name}"
        datadog_api_key = "${var.datadog_api_key}"
        backup_file = "${var.backup_file}"
    }

    lifecycle {
        create_before_destroy = true
    }
}

###################################################################

resource "aws_launch_configuration" "default" {
    name_prefix = "${var.name}-${var.version}-"
    image_id = "${var.ami_id}"
    instance_type = "${var.instance_type}"
    iam_instance_profile = "${var.iam_instance_profile}"
    ebs_optimized = "${var.ebs_optimized}"
    enable_monitoring = false
    key_name = "${var.key_name}"
    security_groups = ["${split(",", var.security_groups)}"]
    user_data = "${template_file.user_data.rendered}"

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
        value = "${var.name}-${var.version}"
        propagate_at_launch = true
    }

    tag {
        key = "DBSilo"
        value = "${var.dbsilo_name}-redis"
        propagate_at_launch = true
    }

    lifecycle {
        create_before_destroy = true
    }
}
