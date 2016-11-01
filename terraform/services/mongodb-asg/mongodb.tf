variable "subnet_ids" {
    type = "list"
}
variable "zone_name" {}
variable "security_groups" {
    type = "list"
}

###################################################################

variable "name" {}
variable "version" {}
variable "service" {}
variable "replica_set" {
    default = ""
}
variable "env" {}
variable "datadog_api_key" {}

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

variable "snapshot_id" {}

###################################################################

data "template_file" "user_data" {
    template = "${file("${path.module}/user-data.sh")}"

    vars {
        app = "navopt",
        env = "${var.env}"
        service = "${var.service}"
        replica_set = "${coalesce(var.replica_set, var.service)}"
        type = "mongo"
        zone_name = "${var.zone_name}"
        datadog_api_key = "${var.datadog_api_key}"
        snapshot_id = "${var.snapshot_id}"
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
    security_groups = ["${var.security_groups}"]
    user_data = "${data.template_file.user_data.rendered}"

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_autoscaling_group" "default" {
    name = "${var.name}"

    launch_configuration = "${aws_launch_configuration.default.name}"
    min_size = "${var.min_size}"
    max_size = "${var.max_size}"
    desired_capacity = "${var.desired_capacity}"
    termination_policies = ["OldestInstance", "ClosestToNextInstanceHour"]
    vpc_zone_identifier = ["${var.subnet_ids}"]

    tag {
        key = "Name"
        value = "${var.name}-${var.version}"
        propagate_at_launch = true
    }

    tag {
        key = "Service"
        value = "${var.service}"
        propagate_at_launch = true
    }

    tag {
        key = "Type"
        value = "mongo"
        propagate_at_launch = true
    }

    lifecycle {
        create_before_destroy = true
    }
}
