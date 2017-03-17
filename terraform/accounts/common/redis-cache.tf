module "redis-cache" {
    source = "../../services/redis-asg"

    name = "redis-cache"
    key_name = "${var.key_name}"

    vpc_id = "${var.vpc_id}"
    private_cidrs = ["${var.private_cidrs}"]
    subnet_ids = "${var.private_subnet_ids}"
    zone_id = "${var.dns_zone_id}"
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

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}
