module "redis-cache" {
    source = "../../services/redis"

    name = "redis-cache"
    key_name = "${var.key_name}"
    iam_instance_profile = "${module.iam.redis_instance_profile}"

    subnet_ids = "${var.private_subnet_ids}"
    security_groups = "${module.sg.redis_security_groups}"
    zone_name = "${var.dns_zone_name}"

    version = "${var.redis_cache_version}"
    ami_id = "${var.redis_cache_ami}"
    instance_type = "${var.redis_cache_instance_type}"
    ebs_optimized = false
    min_size = "${var.redis_cache_min_size}"
    max_size = "${var.redis_cache_max_size}"
    desired_capacity = "${var.redis_cache_desired_capacity}"
    quorum_size = "${var.redis_cache_quorum_size}"

    env = "${var.env}"
    service = "redis-cache"
    datadog_api_key = "${var.datadog_api_key}"
}
