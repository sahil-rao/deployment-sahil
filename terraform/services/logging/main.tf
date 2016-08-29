module "elasticsearch" {
    source = "../elasticsearch"

    env = "${var.env}"
    name = "${var.elasticsearch_name}"

    region = "${var.region}"
    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = ["${var.subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"

    security_groups = ["${var.elasticsearch_security_groups}"]

    ami = "${var.elasticsearch_ami}"
    instance_type = "${var.elasticsearch_instance_type}"
    instance_count = "${var.elasticsearch_instance_count}"
    key_name = "${var.key_name}"
    iam_instance_profile = "${var.elasticsearch_iam_instance_profile}"
    ebs_optimized = "${var.elasticsearch_ebs_optimized}"
}

module "logstash" {
    source = "../logstash"

    env = "${var.env}"
    name = "${var.logstash_name}"

    region = "${var.region}"
    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
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
    source = "../redis"

    name = "${var.redis_name}"
    key_name = "${var.key_name}"
    iam_instance_profile = "${var.redis_iam_instance_profile}"

    subnet_ids = ["${var.subnet_ids}"]
    security_groups = ["${var.redis_security_groups}"]
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
}
