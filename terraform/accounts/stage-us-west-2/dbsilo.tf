module "dbsilo1" {
    source = "../../services/dbsilo"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo1"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo1-mongo"
    mongo_replica_set = "dbsilo1"
    mongo_iam_instance_profile = "${module.common.mongo_instance_profile}"
    mongo_security_groups = ["${module.common.mongo_security_groups}"]
    mongo_version = "v22"
    mongo_ami_id = "ami-d930e0b9"
    mongo_instance_type = "t2.micro"
    mongo_min_size = 0
    mongo_max_size = 3
    mongo_desired_capacity = 1
    mongo_ebs_optimized = false

    redis_name = "${var.cluster_name}-dbsilo1-redis"
    redis_iam_instance_profile = "${module.common.redis_instance_profile}"
    redis_security_groups = ["${module.common.redis_security_groups}"]
    redis_version = "v18"
    redis_ami_id = "ami-b70fdfd7"
    redis_instance_type = "t2.micro"
    redis_min_size = 0
    redis_max_size = 3
    redis_desired_capacity = 1
    redis_ebs_optimized = false
    redis_quorum_size = 2

    elasticsearch_name = "${var.cluster_name}-dbsilo1-elasticsearch"
    elasticsearch_iam_instance_profile = "${module.common.elasticsearch_instance_profile}"
    elasticsearch_security_groups = ["${module.common.elasticsearch_security_groups}"]
    elasticsearch_version = "v11"
    elasticsearch_ami_id = "ami-6b0ede0b"
    #elasticsearch_instance_type = "m3.xlarge"
    elasticsearch_instance_type = "t2.micro"
    elasticsearch_min_size = 0
    elasticsearch_max_size = 3
    elasticsearch_desired_capacity = 1
    elasticsearch_ebs_optimized = false

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}
