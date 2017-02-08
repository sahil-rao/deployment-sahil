data "aws_ami" "ecs" {
    most_recent = true
    filter {
        name = "name"
        values = ["amzn-ami-2016.09.d-amazon-ecs-optimized"]
    }
    owners = ["amazon"]
}

data "template_file" "user_data" {
    template = "${file("${path.module}/user_data.sh")}"

    vars {
        cluster_name = "${aws_ecs_cluster.default.name}"
    }
}

resource "aws_launch_configuration" "ecs" {
    name_prefix = "${var.name}-"
    image_id = "${data.aws_ami.ecs.image_id}"
    instance_type = "${var.instance_type}"
    key_name = "${var.key_name}"
    security_groups = ["${aws_security_group.ecs.id}"]
    iam_instance_profile = "${aws_iam_instance_profile.ecs.name}"
    user_data = "${data.template_file.user_data.rendered}"

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_autoscaling_group" "ecs" {
    name = "${var.name}"
    launch_configuration = "${aws_launch_configuration.ecs.name}"
    min_size = "${var.min_size}"
    max_size = "${var.max_size}"
    desired_capacity = "${var.desired_capacity}"
    vpc_zone_identifier = ["${var.subnet_ids}"]
    termination_policies = ["OldestLaunchConfiguration", "ClosestToNextInstanceHour"]

    tag {
        key = "Name"
        value = "${var.name}-${var.version}"
        propagate_at_launch = true
    }
}
