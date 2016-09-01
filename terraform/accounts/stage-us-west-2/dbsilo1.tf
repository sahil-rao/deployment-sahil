module "dbsilo1" {
    source = "../../services/dbsilo"

    vpc_id = "${terraform_remote_state.networking.output.vpc_id}"
    vpc_cidr = "${terraform_remote_state.networking.output.vpc_cidr}"
    subnet_ids = "${terraform_remote_state.networking.output.private_subnet_ids}"
    zone_name = "${terraform_remote_state.networking.output.zone_name}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo1"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo1-mongo"
    mongo_iam_instance_profile = "${module.iam.mongo_instance_profile}"
    mongo_security_groups = "${module.sg.mongo_security_groups}"
    mongo_version = "v6"
    mongo_ami_id = "ami-d8ce07b8"
    #mongo_instance_type = "m4.xlarge"
    mongo_instance_type = "t2.micro"
    mongo_min_size = 0
    mongo_max_size = 3
    mongo_desired_capacity = 3
    mongo_ebs_optimized = false

    redis_name = "${var.cluster_name}-dbsilo1-redis"
    redis_iam_instance_profile = "${module.iam.redis_instance_profile}"
    redis_security_groups = "${module.sg.redis_security_groups}"
    redis_version = "v4"
    redis_ami_id = "ami-d0ad63b0"
    #redis_instance_type = "r3.2xlarge"
    redis_instance_type = "t2.micro"
    redis_min_size = 0
    redis_max_size = 3
    redis_desired_capacity = 0
    redis_ebs_optimized = false

    elasticsearch_name = "${var.cluster_name}-dbsilo1-elasticsearch"
    elasticsearch_iam_instance_profile = "${module.iam.elasticsearch_instance_profile}"
    elasticsearch_security_groups = "${module.sg.elasticsearch_security_groups}"
    elasticsearch_version = "v4"
    elasticsearch_ami_id = "ami-7eab651e"
    #elasticsearch_instance_type = "m3.xlarge"
    elasticsearch_instance_type = "t2.micro"
    elasticsearch_min_size = 0
    elasticsearch_max_size = 3
    elasticsearch_desired_capacity = 0
    elasticsearch_ebs_optimized = false
}
