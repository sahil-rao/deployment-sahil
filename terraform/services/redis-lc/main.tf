variable "name" {}
variable "version" {}

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

variable "cloudwatch_retention_in_days" {}
variable "log_subscription_destination_arn" {}

###################################################################

module "redis-service" {
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
        type = "redis"
        zone_name = "${var.zone_name}"
        datadog_api_key = "${var.datadog_api_key}"
        redis_backup_file = "${var.backup_file}"
        redis_quorum_size = "${var.quorum_size}"
        redis_backups_enabled = "${var.backups_enabled}"
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

###################################################################

output "name" {
    value = "${aws_launch_configuration.default.name}"
}
