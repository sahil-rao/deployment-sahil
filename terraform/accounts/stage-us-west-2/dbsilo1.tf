module "dbsilo1" {
    source = "../../services/dbsilo"

    vpc_id = "${terraform_remote_state.networking.output.vpc_id}"
    vpc_cidr = "${terraform_remote_state.networking.output.vpc_cidr}"
    subnet_ids = "${terraform_remote_state.networking.output.private_subnet_ids}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo1"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo1-mongo"
    mongo_iam_instance_profile = "${module.iam.mongo_instance_profile}"
    mongo_security_groups = "${module.sg.mongo_security_groups}"

    mongo_blue_version = "v2"
    mongo_blue_ami_id = "ami-32d11c52"
    #mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_instance_type = "t2.micro"
    mongo_blue_min_size = 1
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 1
    mongo_blue_ebs_optimized = false

    mongo_green_version = "v1"
    mongo_green_ami_id = "ami-32d11c52"
    #mongo_green_instance_type = "m4.xlarge"
    mongo_green_instance_type = "t2.micro"
    mongo_green_min_size = 0
    mongo_green_max_size = 0
    mongo_green_desired_capacity = 0
    mongo_green_ebs_optimized = false

    redis_name = "${var.cluster_name}-dbsilo1-redis"
    redis_iam_instance_profile = "${module.iam.redis_instance_profile}"
    redis_security_groups = "${module.sg.redis_security_groups}"

    redis_blue_version = "v2"
    redis_blue_ami_id = "ami-fad71a9a"
    #redis_blue_instance_type = "r3.2xlarge"
    redis_blue_instance_type = "t2.micro"
    redis_blue_min_size = 1
    redis_blue_max_size = 3
    redis_blue_desired_capacity = 3
    redis_blue_ebs_optimized = false

    redis_green_version = "v1"
    redis_green_ami_id = "ami-fad71a9a"
    #redis_green_instance_type = "r3.2xlarge"
    redis_green_instance_type = "t2.micro"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0
    redis_green_ebs_optimized = false

    elasticsearch_name = "${var.cluster_name}-dbsilo1-elasticsearch"
    elasticsearch_iam_instance_profile = "${module.iam.elasticsearch_instance_profile}"
    elasticsearch_security_groups = "${module.sg.elasticsearch_security_groups}"

    elasticsearch_blue_version = "v2"
    elasticsearch_blue_ami_id = "ami-ced31eae"
    #elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_instance_type = "t2.micro"
    elasticsearch_blue_min_size = 3
    elasticsearch_blue_max_size = 3
    elasticsearch_blue_desired_capacity = 3
    elasticsearch_blue_ebs_optimized = false

    elasticsearch_green_version = "v1"
    elasticsearch_green_ami_id = "ami-ced31eae"
    #elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_instance_type = "t2.micro"
    elasticsearch_green_min_size = 0
    elasticsearch_green_max_size = 0
    elasticsearch_green_desired_capacity = 0
    elasticsearch_green_ebs_optimized = false
}
