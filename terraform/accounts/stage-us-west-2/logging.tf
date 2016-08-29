module "logging" {
    source = "../../services/logging"

    region = "${var.region}"
    env = "${var.env}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    elasticsearch_name = "kibana-and-elasticsearch"
    elasticsearch_security_groups = ["${module.sg.elasticsearch_security_groups}"]
    elasticsearch_iam_instance_profile = "${module.iam.elasticsearch_instance_profile}"
    elasticsearch_instance_type = "t2.micro"
    elasticsearch_instance_count = 1

    logstash_name = "logstash"
    logstash_security_groups = ["${module.sg.logstash_security_groups}"]
    logstash_iam_instance_profile = "${module.iam.logstash_instance_profile}"
    logstash_instance_type = "t2.micro"
    logstash_instance_count = 1

    redis_name = "redis-log"
    redis_service = "redis-log"
    redis_security_groups = ["${module.sg.redis_security_groups}"]
    redis_iam_instance_profile = "${module.iam.redis_instance_profile}"

    redis_version = "v4"
    redis_ami_id = "ami-ff10c49f"
    redis_instance_type = "t2.micro"
    redis_min_size = 0
    redis_max_size = 1
    redis_desired_capacity = 1
    redis_quorum_size = 1

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    dns_zone_id = "${data.terraform_remote_state.networking.zone_id}"

    key_name = "${var.key_name}"

    datadog_api_key = "${var.datadog_api_key}"
}
