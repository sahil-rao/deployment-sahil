variable "cloudwatch_retention_in_days" {}
variable "log_subscription_destination_arn" {}

module "elasticsearch" {
    source = "../elasticsearch-asg"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.subnet_ids}"]
    private_cidrs = ["${var.private_cidrs}"]
    zone_id = "${var.dns_zone_id}"
    zone_name = "${var.zone_name}"

    key_name = "${var.key_name}"

    name = "${var.elasticsearch_name}"
    version = "${var.elasticsearch_version}"
    env = "${var.env}"
    service = "${var.elasticsearch_name}"
    datadog_api_key = "${var.datadog_api_key}"

    ami_id = "${var.elasticsearch_ami_id}"
    instance_type = "${var.elasticsearch_instance_type}"
    min_size = "${var.elasticsearch_min_size}"
    max_size = "${var.elasticsearch_max_size}"
    desired_capacity = "${var.elasticsearch_desired_capacity}"
    ebs_optimized = "${var.elasticsearch_ebs_optimized}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "kibana" {
    source = "../kibana"

    env = "${var.env}"
    name = "${var.kibana_name}"

    region = "${var.region}"
    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"

    security_groups = ["${var.kibana_security_groups}"]

    ami = "${var.kibana_ami}"
    instance_type = "${var.kibana_instance_type}"
    instance_count = "${var.kibana_instance_count}"
    key_name = "${var.key_name}"
    iam_instance_profile = "${var.kibana_iam_instance_profile}"
    ebs_optimized = "${var.kibana_ebs_optimized}"
}

module "logstash" {
    source = "../logstash"

    env = "${var.env}"
    name = "${var.logstash_name}"

    region = "${var.region}"
    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"

    security_groups = ["${var.logstash_security_groups}"]

    ami = "${var.logstash_ami}"
    instance_type = "${var.logstash_instance_type}"
    instance_count = "${var.logstash_instance_count}"
    key_name = "${var.key_name}"
    iam_instance_profile = "${var.logstash_iam_instance_profile}"
    ebs_optimized = "${var.logstash_ebs_optimized}"
}

module "redis-log" {
    source = "../redis-asg"

    name = "${var.redis_name}"
    key_name = "${var.key_name}"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.subnet_ids}"]
    private_cidrs = ["${var.private_cidrs}"]
    zone_id = "${var.dns_zone_id}"
    zone_name = "${var.zone_name}"

    ami_id = "${var.redis_ami_id}"
    version = "${var.redis_version}"
    instance_type = "${var.redis_instance_type}"
    ebs_optimized = "${var.redis_ebs_optimized}"
    min_size = "${var.redis_min_size}"
    max_size = "${var.redis_max_size}"
    desired_capacity = "${var.redis_desired_capacity}"
    quorum_size = "${var.redis_quorum_size}"

    env = "${var.env}"
    version = "${var.redis_version}"
    service = "${var.redis_service}"
    datadog_api_key = "${var.datadog_api_key}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${var.log_subscription_destination_arn}"
}
