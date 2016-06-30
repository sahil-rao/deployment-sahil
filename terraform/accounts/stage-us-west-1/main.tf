provider "aws" {
    profile = "navopt_prod"
    region = "${var.region}"
}

module "dbsilo1" {
    source = "../../dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.cluster_name}-dbsilo1"
    dbsilo_name = "dbsilo1"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_blue_name_prefix = "${var.cluster_name}-dbsilo1-mongo-blue"
    mongo_blue_ami_id = "ami-a699ddc6"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 1
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 3

    mongo_green_name_prefix = "${var.cluster_name}-dbsilo1-mongo-green"
    mongo_green_ami_id = "ami-1ca7e37c"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 1
    mongo_green_max_size = 3
    mongo_green_desired_capacity = 3

    redis_blue_name_prefix = "${var.cluster_name}-dbsilo1-redis-blue-v2"
    redis_blue_ami_id = "ami-cfa0e4af"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 0
    redis_blue_max_size = 0
    redis_blue_desired_capacity = 0

    redis_green_name_prefix = "${var.cluster_name}-dbsilo1-redis-green-v1"
    redis_green_ami_id = "ami-cfa0e4af"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0

    elasticsearch_blue_name_prefix = "${var.cluster_name}-dbsilo1-elasticsearch-blue-v2"
    elasticsearch_blue_ami_id = "ami-01a7e361"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 0
    elasticsearch_blue_max_size = 0
    elasticsearch_blue_desired_capacity = 0

    elasticsearch_green_name_prefix = "${var.cluster_name}-dbsilo1-elasticsearch-green-v1"
    elasticsearch_green_ami_id = "ami-01a7e361"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
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

    mongo_blue_name_prefix = "${var.cluster_name}-dbsilo2-mongo-blue"
    mongo_blue_ami_id = "ami-a699ddc6"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 1
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 3

    # WARNING: Update version number if AMI is changed
    mongo_green_name_prefix = "${var.cluster_name}-dbsilo2-mongo-green-v2"
    mongo_green_ami_id = "ami-1ca7e37c"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 1
    mongo_green_max_size = 3
    mongo_green_desired_capacity = 3

    redis_blue_name_prefix = "${var.cluster_name}-dbsilo2-redis-blue-v2"
    redis_blue_ami_id = "ami-cfa0e4af"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 0
    redis_blue_max_size = 0
    redis_blue_desired_capacity = 0

    redis_green_name_prefix = "${var.cluster_name}-dbsilo2-redis-green-v1"
    redis_green_ami_id = "ami-cfa0e4af"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0

    # WARNING: please update version number if ami changes
    elasticsearch_blue_name_prefix = "${var.cluster_name}-dbsilo2-elasticsearch-blue-v2"
    elasticsearch_blue_ami_id = "ami-01a7e361"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 0
    elasticsearch_blue_max_size = 0
    elasticsearch_blue_desired_capacity = 0

    elasticsearch_green_name_prefix = "${var.cluster_name}-dbsilo2-elasticsearch-green-v1"
    elasticsearch_green_ami_id = "ami-01a7e361"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
}

module "dbsilo4" {
    source = "../../dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.cluster_name}-dbsilo4"
    dbsilo_name = "dbsilo4"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_blue_name_prefix = "${var.cluster_name}-dbsilo4-mongo-blue-v2"
    mongo_blue_ami_id = "ami-a699ddc6"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 1
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 3

    mongo_green_name_prefix = "${var.cluster_name}-dbsilo4-mongo-green-v3"
    mongo_green_ami_id = "ami-a699ddc6"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 3
    mongo_green_max_size = 3
    mongo_green_desired_capacity = 3

    redis_blue_name_prefix = "${var.cluster_name}-dbsilo4-redis-blue-v2"
    redis_blue_ami_id = "ami-179eda77"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 0
    redis_blue_max_size = 0
    redis_blue_desired_capacity = 0
    redis_blue_backup_file = ""

    redis_green_name_prefix = "${var.cluster_name}-dbsilo4-redis-green-v3"
    redis_green_ami_id = "ami-8b3671eb"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 3
    redis_green_max_size = 3
    redis_green_desired_capacity = 3
    redis_green_backup_file = ""

    # WARNING: please update version number if ami changes
    elasticsearch_blue_name_prefix = "${var.cluster_name}-dbsilo4-elasticsearch-blue-v3"
    elasticsearch_blue_ami_id = "ami-01a7e361"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 3
    elasticsearch_blue_max_size = 3
    elasticsearch_blue_desired_capacity = 3

    elasticsearch_green_name_prefix = "${var.cluster_name}-dbsilo4-elasticsearch-green-v2"
    elasticsearch_green_ami_id = "ami-01a7e361"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
}
