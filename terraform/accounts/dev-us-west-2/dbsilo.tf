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
    mongo_version = "v2"
    mongo_ami_id = "ami-4bc0162b"
    mongo_instance_type = "m4.xlarge"
    mongo_min_size = 0
    mongo_max_size = 3
    mongo_desired_capacity = 3
    mongo_ebs_optimized = false

    redis_name = "${var.cluster_name}-dbsilo1-redis"
    redis_iam_instance_profile = "${module.common.redis_instance_profile}"
    redis_security_groups = ["${module.common.redis_security_groups}"]
    redis_version = "v3"
    redis_ami_id = "ami-4bdf092b"
    redis_instance_type = "r3.2xlarge"
    redis_min_size = 0
    redis_max_size = 3
    redis_desired_capacity = 3
    redis_ebs_optimized = false
    redis_quorum_size = 2
    redis_backups_enabled = true
    redis_backup_file = "s3://xplain-alpha/dbsilo1/redis-backups/dump2016-10-18T01:05:01+0000.rdb"

    elasticsearch_name = "${var.cluster_name}-dbsilo1-elasticsearch"
    elasticsearch_iam_instance_profile = "${module.common.elasticsearch_instance_profile}"
    elasticsearch_security_groups = ["${module.common.elasticsearch_security_groups}"]
    elasticsearch_version = "v1"
    elasticsearch_ami_id = "ami-23d00643"
    #elasticsearch_instance_type = "m3.xlarge"
    elasticsearch_instance_type = "t2.micro"
    elasticsearch_min_size = 0
    elasticsearch_max_size = 3
    elasticsearch_desired_capacity = 3
    elasticsearch_ebs_optimized = false
}

module "dbsilo2" {
    source = "../../services/dbsilo"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo2"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo2-mongo"
    mongo_replica_set = "dbsilo2"
    mongo_iam_instance_profile = "${module.common.mongo_instance_profile}"
    mongo_security_groups = ["${module.common.mongo_security_groups}"]
    mongo_version = "v2"
    mongo_ami_id = "ami-4bc0162b"
    mongo_instance_type = "m4.xlarge"
    mongo_min_size = 0
    mongo_max_size = 3
    mongo_desired_capacity = 3
    mongo_ebs_optimized = false

    redis_name = "${var.cluster_name}-dbsilo2-redis"
    redis_iam_instance_profile = "${module.common.redis_instance_profile}"
    redis_security_groups = ["${module.common.redis_security_groups}"]
    redis_version = "v3"
    redis_ami_id = "ami-4bdf092b"
    redis_instance_type = "r3.2xlarge"
    redis_min_size = 0
    redis_max_size = 3
    redis_desired_capacity = 3
    redis_ebs_optimized = false
    redis_quorum_size = 2
    redis_backups_enabled = true
    redis_backup_file = "s3://xplain-alpha/dbsilo2/redis-backups/dump2016-10-18T01:05:01+0000.rdb"

    elasticsearch_name = "${var.cluster_name}-dbsilo2-elasticsearch"
    elasticsearch_iam_instance_profile = "${module.common.elasticsearch_instance_profile}"
    elasticsearch_security_groups = ["${module.common.elasticsearch_security_groups}"]
    elasticsearch_version = "v1"
    elasticsearch_ami_id = "ami-23d00643"
    #elasticsearch_instance_type = "m3.xlarge"
    elasticsearch_instance_type = "t2.micro"
    elasticsearch_min_size = 0
    elasticsearch_max_size = 3
    elasticsearch_desired_capacity = 3
    elasticsearch_ebs_optimized = false
}
