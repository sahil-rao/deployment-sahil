module "logging" {
    source = "../../services/logging"

    region = "${var.region}"
    env = "${var.env}"

    elasticsearch_name = "kibana-and-elasticsearch"
    elasticsearch_security_groups = "${module.sg.elasticsearch_security_groups}"
    elasticsearch_iam_instance_profile = "${module.iam.elasticsearch_instance_profile}"
    elasticsearch_instance_type = "t2.micro"
    elasticsearch_instance_count = 1

    logstash_name = "logstash"
    logstash_security_groups = "${module.sg.logstash_security_groups}"
    logstash_iam_instance_profile = "${module.iam.logstash_instance_profile}"
    logstash_instance_type = "t2.micro"
    logstash_instance_count = 1

    redis_name = "redis-log"
    redis_security_groups = "${module.sg.redis_security_groups}"
    redis_iam_instance_profile = "${module.iam.redis_instance_profile}"
    redis_instance_type = "t2.micro"
    redis_instance_count = 1

    vpc_id = "${terraform_remote_state.networking.output.vpc_id}"
    vpc_cidr = "${terraform_remote_state.networking.output.vpc_cidr}"
    subnet_ids = "${terraform_remote_state.networking.output.private_subnet_ids}"
    dns_zone_id = "${terraform_remote_state.networking.output.zone_id}"

    key_name = "${var.key_name}"
}
