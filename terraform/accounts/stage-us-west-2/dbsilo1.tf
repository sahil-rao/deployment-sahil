module "dbsilo1" {
    source = "../../services/dbsilo"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = "${data.terraform_remote_state.networking.private_subnet_ids}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    dbsilo_name = "dbsilo1"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_name = "${var.cluster_name}-dbsilo1-mongo"
    mongo_iam_instance_profile = "${module.iam.mongo_instance_profile}"
    mongo_security_groups = "${module.sg.mongo_security_groups}"
    mongo_version = "v10"
    mongo_ami_id = "ami-fe965e9e"
    #mongo_instance_type = "m4.xlarge"
    mongo_instance_type = "t2.micro"
    mongo_min_size = 3
    mongo_max_size = 3
    mongo_desired_capacity = 3
    mongo_ebs_optimized = false

    redis_name = "${var.cluster_name}-dbsilo1-redis"
    redis_iam_instance_profile = "${module.iam.redis_instance_profile}"
    redis_security_groups = "${module.sg.redis_security_groups}"
    redis_version = "v8"
    redis_ami_id = "ami-c6d41da6"
    #redis_instance_type = "r3.2xlarge"
    redis_instance_type = "t2.micro"
    redis_min_size = 0
    redis_max_size = 6
    redis_desired_capacity = 6
    redis_ebs_optimized = false

    elasticsearch_name = "${var.cluster_name}-dbsilo1-elasticsearch"
    elasticsearch_iam_instance_profile = "${module.iam.elasticsearch_instance_profile}"
    elasticsearch_security_groups = "${module.sg.elasticsearch_security_groups}"
    elasticsearch_version = "v7"
    elasticsearch_ami_id = "ami-3310d953"
    #elasticsearch_instance_type = "m3.xlarge"
    elasticsearch_instance_type = "t2.micro"
    elasticsearch_min_size = 0
    elasticsearch_max_size = 6
    elasticsearch_desired_capacity = 6
    elasticsearch_ebs_optimized = false
}
