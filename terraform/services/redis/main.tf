variable "cloudwatch_retention_in_days" {}
variable "log_subscription_destination_arn" {}

module "redis-lc" {
    source = "../redis-lc"

    name = "${var.name}"
    version = "${var.version}"

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.iam_instance_profile}"

    zone_name = "${var.zone_name}"
    security_groups = "${var.security_groups}"

    ami_id = "${var.ami_id}"
    instance_type = "${var.instance_type}"
    ebs_optimized = "${var.ebs_optimized}"
    quorum_size = "${var.quorum_size}"
    backup_file = "${var.backup_file}"
    backups_enabled = "${var.backups_enabled}"

    env = "${var.env}"
    service = "${var.service}"
    datadog_api_key = "${var.datadog_api_key}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "redis-asg" {
    source = "../redis-asg"

    name = "${var.name}"
    version = "${var.version}"
    launch_configuration = "${module.redis-lc.name}"
    subnet_ids = "${var.subnet_ids}"

    env = "${var.env}"
    service = "${var.service}"

    min_size = "${var.min_size}"
    max_size = "${var.max_size}"
    desired_capacity = "${var.desired_capacity}"
}
