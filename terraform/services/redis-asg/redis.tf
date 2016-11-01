variable "name" {}
variable "version" {}
variable "launch_configuration" {}
variable "subnet_ids" {
    type = "list"
}

variable "min_size" {}
variable "max_size" {}
variable "desired_capacity" {}

variable "env" {}
variable "service" {}

###################################################################

resource "aws_autoscaling_group" "default" {
    name = "${var.name}"
    launch_configuration = "${var.launch_configuration}"
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
        key = "Env"
        value = "${var.env}"
        propagate_at_launch = true
    }

    tag {
        key = "Service"
        value = "${var.service}"
        propagate_at_launch = true
    }

    tag {
        key = "Type"
        value = "redis"
        propagate_at_launch = true
    }

    lifecycle {
        create_before_destroy = true
    }
}
