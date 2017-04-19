module "dbsilo1" {
    source = "../../services/dbsilo"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.all_access_cidrs}",
    ]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo1"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo1-mongo"
    mongo_replica_set = "dbsilo1"
    mongo_version = "v013"
    mongo_ami_id = "ami-3f50c55f"
    mongo_instance_type = "m4.xlarge"
    mongo_min_size = 0
    mongo_max_size = 5
    mongo_desired_capacity = 5
    mongo_ebs_optimized = false

    redis_name = "${var.cluster_name}-dbsilo1-redis"
    redis_version = "v013"
    redis_ami_id = "ami-3d50c55d"
    redis_instance_type = "r3.2xlarge"
    redis_min_size = 0
    redis_max_size = 5
    redis_desired_capacity = 5
    redis_ebs_optimized = false
    redis_quorum_size = 2
    redis_backups_enabled = true

    elasticsearch_name = "${var.cluster_name}-dbsilo1-elasticsearch"
    elasticsearch_version = "v013"
    elasticsearch_ami_id = "ami-1252c772"
    elasticsearch_instance_type = "t2.medium"
    elasticsearch_min_size = 0
    elasticsearch_max_size = 3
    elasticsearch_desired_capacity = 3
    elasticsearch_ebs_optimized = false
    elasticsearch_heap_size = "2g"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}

module "dbsilo2" {
    source = "../../services/dbsilo"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.all_access_cidrs}",
    ]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo2"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo2-mongo"
    mongo_replica_set = "dbsilo2"
    mongo_version = "v013"
    mongo_ami_id = "ami-3f50c55f"
    mongo_instance_type = "m4.xlarge"
    mongo_min_size = 0
    mongo_max_size = 5
    mongo_desired_capacity = 5
    mongo_ebs_optimized = false

    redis_name = "${var.cluster_name}-dbsilo2-redis"
    redis_version = "v013"
    redis_ami_id = "ami-3d50c55d"
    redis_instance_type = "r3.2xlarge"
    redis_min_size = 0
    redis_max_size = 5
    redis_desired_capacity = 5
    redis_ebs_optimized = false
    redis_quorum_size = 2
    redis_backups_enabled = true

    elasticsearch_name = "${var.cluster_name}-dbsilo2-elasticsearch"
    elasticsearch_version = "v013"
    elasticsearch_ami_id = "ami-1252c772"
    elasticsearch_instance_type = "t2.medium"
    elasticsearch_min_size = 0
    elasticsearch_max_size = 3
    elasticsearch_desired_capacity = 3
    elasticsearch_ebs_optimized = false
    elasticsearch_heap_size = "2g"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}
