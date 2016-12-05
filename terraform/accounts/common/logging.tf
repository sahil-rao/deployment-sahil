module "log-service" {
    source = "../../modules/log-service"

    environment = "${var.env}"
}

module "logging" {
    source = "../../services/logging"

    region = "${var.region}"
    env = "${var.env}"
    zone_name = "${var.dns_zone_name}"

    kibana_name = "logging-kibana"
    kibana_security_groups = ["${module.sg.kibana_security_groups}"]
    kibana_iam_instance_profile = "${module.iam.kibana_instance_profile}"
    kibana_instance_type = "t2.micro"
    kibana_instance_count = 1

    elasticsearch_name = "logging-elastic"
    elasticsearch_security_groups = ["${module.sg.elasticsearch_security_groups}"]
    elasticsearch_iam_instance_profile = "${module.iam.elasticsearch_instance_profile}"
    elasticsearch_version = "${var.logging_elasticsearch_version}"
    elasticsearch_ami_id = "${var.logging_elasticsearch_ami}"
    elasticsearch_instance_type = "${var.logging_elasticsearch_instance_type}"
    elasticsearch_min_size = "${var.logging_elasticsearch_min_size}"
    elasticsearch_max_size = "${var.logging_elasticsearch_max_size}"
    elasticsearch_desired_capacity = "${var.logging_elasticsearch_desired_capacity}"
    elasticsearch_ebs_optimized = false

    logstash_name = "logging-logstash"
    logstash_security_groups = ["${module.sg.logstash_security_groups}"]
    logstash_iam_instance_profile = "${module.iam.logstash_instance_profile}"
    logstash_instance_type = "t2.micro"
    logstash_instance_count = 1

    redis_name = "logging-redis"
    redis_service = "redis-log"
    redis_security_groups = ["${module.sg.redis_security_groups}"]
    redis_iam_instance_profile = "${module.iam.redis_instance_profile}"

    redis_version = "${var.logging_redis_version}"
    redis_ami_id = "${var.logging_redis_ami}"
    redis_instance_type = "${var.logging_redis_instance_type}"
    redis_min_size = "${var.logging_redis_min_size}"
    redis_max_size = "${var.logging_redis_max_size}"
    redis_desired_capacity = "${var.logging_redis_desired_capacity}"
    redis_quorum_size = "${var.logging_redis_quorum_size}"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.private_subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"

    key_name = "${var.key_name}"

    datadog_api_key = "${var.datadog_api_key}"
}
