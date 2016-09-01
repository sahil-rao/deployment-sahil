variable "name_prefix" {}

variable "key_name" {}
variable "iam_instance_profile" {}
variable "security_groups" {
    type = "list"
}

variable "ami_id" {}
variable "instance_type" {}
variable "ebs_optimized" {
    default = true
}
variable "backup_file" {
    default = ""
}

variable "env" {}
variable "service" {}
variable "zone_name" {}

variable "datadog_api_key" {}
variable "quorum_size" {}
variable "backups_enabled" {
    default = false
}

###################################################################

data "template_file" "user_data" {
    template = "${file("${path.module}/user-data.sh")}"

    vars {
        application = "navopt"
        env = "${var.env}"
        service = "${var.service}"
        zone_name = "${var.zone_name}"
        datadog_api_key = "${var.datadog_api_key}"
        redis_backup_file = "${var.backup_file}"
        redis_quorum_size = "${var.quorum_size}"
        redis_backups_enabled = "${var.backups_enabled}"
    }
}

###################################################################

resource "aws_launch_configuration" "default" {
    name_prefix = "${var.name_prefix}"
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

###################################################################

output "name" {
    value = "${aws_launch_configuration.default.name}"
}
