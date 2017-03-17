module "elasticsearch-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "${var.name}"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

###################################################################

data "template_file" "user_data" {
    template = "${file("${path.module}/user-data.sh")}"

    vars {
        app = "navopt"
        env = "${var.env}"
        service = "${var.service}"
        type = "elasticsearch"
        zone_id = "${var.zone_id}"
        zone_name = "${var.zone_name}"
        datadog_api_key = "${var.datadog_api_key}"
        sg_name = "${aws_security_group.elasticsearch.id}"
    }
}

resource "aws_launch_configuration" "default" {
    name = "${var.name}-${var.version}"
    image_id = "${var.ami_id}"
    instance_type = "${var.instance_type}"
    iam_instance_profile = "${aws_iam_instance_profile.elasticsearch.name}"
    ebs_optimized = "${var.ebs_optimized}"
    enable_monitoring = false
    key_name = "${var.key_name}"
    security_groups = ["${aws_security_group.elasticsearch.id}"]
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
        value = "elasticsearch"
        propagate_at_launch = true
    }

    lifecycle {
        create_before_destroy = true
    }
}
