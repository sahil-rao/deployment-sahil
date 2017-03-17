module "mongodb" {
    source = "../mongodb-asg"

    vpc_id = "${var.vpc_id}"
    private_cidrs = ["${var.private_cidrs}"]
    subnet_ids = ["${var.subnet_ids}"]
    zone_id = "${var.zone_id}"
    zone_name = "${var.zone_name}"

    key_name = "${var.key_name}"

    name = "${var.mongo_name}"
    version = "${var.mongo_version}"
    replica_set = "${var.mongo_replica_set}"
    env = "${var.cluster_name}"
    service = "${var.dbsilo_name}-mongo"
    datadog_api_key = "${var.datadog_api_key}"
    snapshot_id = "${var.mongo_snapshot_id}"

    ami_id = "${var.mongo_ami_id}"
    instance_type = "${var.mongo_instance_type}"
    min_size = "${var.mongo_min_size}"
    max_size = "${var.mongo_max_size}"
    desired_capacity = "${var.mongo_desired_capacity}"
    ebs_optimized = "${var.mongo_ebs_optimized}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "redis" {
    source = "../redis-asg"

    subnet_ids = ["${var.subnet_ids}"]
    zone_id = "${var.zone_id}"
    zone_name = "${var.zone_name}"
    security_groups = ["${var.redis_security_groups}"]

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.redis_iam_instance_profile}"

    name = "${var.redis_name}"
    version = "${var.redis_version}"
    env = "${var.cluster_name}"
    service = "${var.dbsilo_name}-redis"
    datadog_api_key = "${var.datadog_api_key}"
    backup_file = "${var.redis_backup_file}"
    quorum_size = "${var.redis_quorum_size}"

    ami_id = "${var.redis_ami_id}"
    instance_type = "${var.redis_instance_type}"
    min_size = "${var.redis_min_size}"
    max_size = "${var.redis_max_size}"
    desired_capacity = "${var.redis_desired_capacity}"
    ebs_optimized = "${var.redis_ebs_optimized}"
    backups_enabled = "${var.redis_backups_enabled}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "elasticsearch" {
    source = "../elasticsearch-asg"

    vpc_id = "${var.vpc_id}"
    private_cidrs = ["${var.private_cidrs}"]
    subnet_ids = ["${var.subnet_ids}"]
    zone_id = "${var.zone_id}"
    zone_name = "${var.zone_name}"

    key_name = "${var.key_name}"

    name = "${var.elasticsearch_name}"
    version = "${var.elasticsearch_version}"
    env = "${var.cluster_name}"
    service = "${var.dbsilo_name}-elasticsearch"
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
