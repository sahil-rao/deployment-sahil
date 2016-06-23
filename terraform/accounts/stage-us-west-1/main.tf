provider "aws" {
    profile = "navopt_prod"
    region = "${var.region}"
}

module "dbsilo4" {
    source = "../../dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "erickt-tf-redis-test"
    dbsilo_name = "dbsilo4"
    cluster_name = "${var.cluster_name}"

    mongo_blue_ami_id = "ami-50400430"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 3
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 3

    mongo_green_ami_id = "ami-50400430"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 0
    mongo_green_max_size = 0
    mongo_green_desired_capacity = 0

    redis_blue_ami_id = "ami-64400404"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 3
    redis_blue_max_size = 3
    redis_blue_desired_capacity = 3

    redis_green_ami_id = "ami-64400404"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0
}