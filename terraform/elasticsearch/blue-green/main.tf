variable "blue_green" {}
variable "ami_id" {}
variable "subnet_ids" {}
variable "security_groups" {}

variable "dbsilo" {}
variable "cluster" {}

variable "min_size" {}
variable "max_size" {}
variable "desired_capacity" {}

resource "template_file" "user_data" {
    template = "${file("${path.module}/user-data.sh")}"

    vars {
        dbsilo = "${var.dbsilo}"
        service = "elasticsearch"
        cluster = "${var.cluster}"
        datadog_api_key = "42bbac658841fd4c44253c01423b3227"
    }

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_launch_configuration" "lc" {
    name_prefix = "prithvi-tf-elastic-lc-test-${var.blue_green}-"
    image_id = "${var.ami_id}"
    instance_type = "m3.xlarge"
    iam_instance_profile = "MongoDB_Server"
    ebs_optimized = true
    enable_monitoring = false
    key_name = "Baaz-Deployment"
    security_groups = ["${split(",", var.security_groups)}"]
    user_data = "${template_file.user_data.rendered}"

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_autoscaling_group" "asg" {
    name = "prithvi-tf-elastic-asg-test-${var.blue_green}"

    launch_configuration = "${aws_launch_configuration.lc.name}"
    min_size = "${var.min_size}"
    max_size = "${var.max_size}"
    desired_capacity = "${var.desired_capacity}"
    vpc_zone_identifier = ["${split(",", var.subnet_ids)}"]
}
