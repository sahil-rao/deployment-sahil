module "logging" {
    source = "../../services/logging"

    region = "${var.region}"
    env = "${var.env}"
    zone_name = "${data.terraform_remote_state.networking.dns_zone_name}"

    kibana_name = "logging-kibana"
    kibana_security_groups = ["${module.sg.kibana_security_groups}"]
    kibana_iam_instance_profile = "${module.iam.kibana_instance_profile}"
    kibana_instance_type = "t2.micro"
    kibana_instance_count = 1

    elasticsearch_name = "logging-elastic"
    elasticsearch_security_groups = ["${module.sg.elasticsearch_security_groups}"]
    elasticsearch_iam_instance_profile = "${module.iam.elasticsearch_instance_profile}"
    elasticsearch_version = "v1"
    elasticsearch_ami_id = "ami-23d00643"
    #elasticsearch_instance_type = "m3.xlarge"
    elasticsearch_instance_type = "t2.micro"
    elasticsearch_min_size = 0
    elasticsearch_max_size = 1
    elasticsearch_desired_capacity = 1
    elasticsearch_ebs_optimized = false

    logstash_name = "logging-logstash"
    logstash_security_groups = ["${module.sg.logstash_security_groups}"]
    logstash_iam_instance_profile = "${module.iam.logstash_instance_profile}"
    logstash_instance_type = "t2.micro"
    logstash_instance_count = 1

    redis_name = "logging-redis"
    redis_service = "redis-log"
    redis_security_groups = ["${module.sg.redis_security_groups}"]
    redis_iam_instance_profile = "${module.iam.redis_instance_profile}"
    redis_version = "v1"
    redis_ami_id = "ami-23d00643"
    redis_instance_type = "t2.micro"
    redis_min_size = 0
    redis_max_size = 1
    redis_desired_capacity = 1
    redis_quorum_size = 1

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    dns_zone_id = "${data.terraform_remote_state.networking.dns_zone_id}"

    key_name = "${var.key_name}"

    datadog_api_key = "${var.datadog_api_key}"
}
