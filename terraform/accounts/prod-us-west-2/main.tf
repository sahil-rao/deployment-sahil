provider "aws" {
    profile = "navopt_prod"
    region = "${var.region}"
}

module "dbsilo2" {
    source = "../../dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.cluster_name}-dbsilo2"
    dbsilo_name = "dbsilo2"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_blue_name_prefix = "${var.cluster_name}-dbsilo2-mongo-blue-v2"
    mongo_blue_ami_id = "ami-8537f0e5"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 0
    mongo_blue_max_size = 0
    mongo_blue_desired_capacity = 0

    mongo_green_name_prefix = "${var.cluster_name}-dbsilo2-mongo-green-v1"
    mongo_green_ami_id = "ami-8537f0e5"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 0
    mongo_green_max_size = 0
    mongo_green_desired_capacity = 0

    redis_blue_name_prefix = "${var.cluster_name}-dbsilo2-redis-blue-v2"
    redis_blue_ami_id = "ami-722dea12"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 0
    redis_blue_max_size = 0
    redis_blue_desired_capacity = 0

    redis_green_name_prefix = "${var.cluster_name}-dbsilo2-redis-green-v1"
    redis_green_ami_id = "ami-722dea12"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0

    elasticsearch_blue_name_prefix = "${var.cluster_name}-dbsilo2-elasticsearch-blue-v1"
    elasticsearch_blue_ami_id = "ami-872ee9e7"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 3
    elasticsearch_blue_max_size = 3
    elasticsearch_blue_desired_capacity = 3

    elasticsearch_green_name_prefix = "${var.cluster_name}-dbsilo2-elasticsearch-green-v1"
    elasticsearch_green_ami_id = "ami-872ee9e7"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
}


module "dbsilo3" {
    source = "../../dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.cluster_name}-dbsilo3"
    dbsilo_name = "dbsilo3"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_blue_name_prefix = "${var.cluster_name}-dbsilo3-mongo-blue-v2"
    mongo_blue_ami_id = "ami-8537f0e5"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 1
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 3

    mongo_green_name_prefix = "${var.cluster_name}-dbsilo3-mongo-green-v1"
    mongo_green_ami_id = "ami-8537f0e5"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 0
    mongo_green_max_size = 0
    mongo_green_desired_capacity = 0

    redis_blue_name_prefix = "${var.cluster_name}-dbsilo3-redis-blue-v2"
    redis_blue_ami_id = "ami-722dea12"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 1
    redis_blue_max_size = 3
    redis_blue_desired_capacity = 3

    redis_green_name_prefix = "${var.cluster_name}-dbsilo3-redis-green-v1"
    redis_green_ami_id = "ami-722dea12"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0

    elasticsearch_blue_name_prefix = "${var.cluster_name}-dbsilo3-elasticsearch-blue-v2"
    elasticsearch_blue_ami_id = "ami-872ee9e7"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 3
    elasticsearch_blue_max_size = 3
    elasticsearch_blue_desired_capacity = 3

    elasticsearch_green_name_prefix = "${var.cluster_name}-dbsilo3-elasticsearch-green-v1"
    elasticsearch_green_ami_id = "ami-872ee9e7"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
}


module "dbsilo5" {
    source = "../../dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.cluster_name}-dbsilo5"
    dbsilo_name = "dbsilo5"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_blue_name_prefix = "${var.cluster_name}-dbsilo5-mongo-blue-v2"
    mongo_blue_ami_id = "ami-8537f0e5"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 1
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 1
    mongo_blue_snapshot_id = "snap-4f3e8308"

    mongo_green_name_prefix = "${var.cluster_name}-dbsilo5-mongo-green-v1"
    mongo_green_ami_id = "ami-8537f0e5"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 0
    mongo_green_max_size = 0
    mongo_green_desired_capacity = 0

    redis_blue_name_prefix = "${var.cluster_name}-dbsilo5-redis-blue-v2"
    redis_blue_ami_id = "ami-722dea12"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 1
    redis_blue_max_size = 3
    redis_blue_desired_capacity = 1
    redis_blue_backup_file = "s3://xplain-app/dbsilo1/redis-backups/dump2016-06-28T23:05:05+0000.rdb"

    redis_green_name_prefix = "${var.cluster_name}-dbsilo5-redis-green-v1"
    redis_green_ami_id = "ami-722dea12"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0

    elasticsearch_blue_name_prefix = "${var.cluster_name}-dbsilo5-elasticsearch-blue-v2"
    elasticsearch_blue_ami_id = "ami-872ee9e7"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 0
    elasticsearch_blue_max_size = 0
    elasticsearch_blue_desired_capacity = 0

    elasticsearch_green_name_prefix = "${var.cluster_name}-dbsilo5-elasticsearch-green-v1"
    elasticsearch_green_ami_id = "ami-872ee9e7"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
}


