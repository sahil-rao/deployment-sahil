provider "aws" {
    profile = "navopt_prod"
    region = "${var.region}"
}

module "dbsilo1" {
    source = "../../services/dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo1"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo1-mongo"

    mongo_blue_version = "${var.cluster_name}-dbsilo1-mongo-blue"
    mongo_blue_ami_id = "ami-a699ddc6"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 1
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 3

    mongo_green_version = "${var.cluster_name}-dbsilo1-mongo-green"
    mongo_green_ami_id = "ami-1ca7e37c"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 0
    mongo_green_max_size = 0
    mongo_green_desired_capacity = 0

    redis_name = "${var.cluster_name}-dbsilo1-redis"

    redis_blue_version = "v2"
    redis_blue_ami_id = "ami-cfa0e4af"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 0
    redis_blue_max_size = 0
    redis_blue_desired_capacity = 0

    redis_green_version = "v1"
    redis_green_ami_id = "ami-cfa0e4af"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0

    elasticsearch_name = "${var.cluster_name}-dbsilo2-elasticsearch"

    elasticsearch_blue_version = "v2"
    elasticsearch_blue_ami_id = "ami-01a7e361"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 0
    elasticsearch_blue_max_size = 0
    elasticsearch_blue_desired_capacity = 0

    elasticsearch_green_version = "v1"
    elasticsearch_green_ami_id = "ami-01a7e361"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
}

module "dbsilo2" {
    source = "../../services/dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo2"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo2-mongo"

    mongo_blue_version = "blue"
    mongo_blue_ami_id = "ami-a699ddc6"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 0
    mongo_blue_max_size = 0
    mongo_blue_desired_capacity = 0

    # WARNING: Update version number if AMI is changed
    mongo_green_version = "v2"
    mongo_green_ami_id = "ami-1ca7e37c"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 1
    mongo_green_max_size = 3
    mongo_green_desired_capacity = 3

    redis_name = "${var.cluster_name}-dbsilo2-redis"

    redis_blue_version = "v2"
    redis_blue_ami_id = "ami-cfa0e4af"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 0
    redis_blue_max_size = 0
    redis_blue_desired_capacity = 0

    redis_green_version = "v1"
    redis_green_ami_id = "ami-cfa0e4af"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0

    elasticsearch_name = "${var.cluster_name}-dbsilo2-elasticsearch"

    # WARNING: please update version number if ami changes
    elasticsearch_blue_version = "v2"
    elasticsearch_blue_ami_id = "ami-01a7e361"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 0
    elasticsearch_blue_max_size = 0
    elasticsearch_blue_desired_capacity = 0

    elasticsearch_green_version = "v1"
    elasticsearch_green_ami_id = "ami-01a7e361"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
}

module "dbsilo4" {
    source = "../../services/dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo4"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo4-mongo"

    mongo_blue_version = "v2"
    mongo_blue_ami_id = "ami-1a5e1f7a"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 0
    mongo_blue_max_size = 0
    mongo_blue_desired_capacity = 0

    mongo_green_version = "v3"
    mongo_green_ami_id = "ami-a699ddc6"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 0
    mongo_green_max_size = 0
    mongo_green_desired_capacity = 0

    redis_name = "${var.cluster_name}-dbsilo4-redis"

    redis_blue_version = "v4"
    redis_blue_ami_id = "ami-8b3671eb"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 0
    redis_blue_max_size = 0
    redis_blue_desired_capacity = 0
    redis_blue_backup_file = ""

    redis_green_version = "v3"
    redis_green_ami_id = "ami-8b3671eb"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0
    redis_green_backup_file = ""

    elasticsearch_name = "${var.cluster_name}-dbsilo4-elasticsearch"

    # WARNING: please update version number if ami changes
    elasticsearch_blue_version = "v3"
    elasticsearch_blue_ami_id = "ami-01a7e361"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 0
    elasticsearch_blue_max_size = 0
    elasticsearch_blue_desired_capacity = 0

    elasticsearch_green_version  = "v2"
    elasticsearch_green_ami_id = "ami-01a7e361"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
}
