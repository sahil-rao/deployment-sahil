/*
module "redis-cache" {
    source = "../../services/redis"

    region = "${var.region}"
    env = "${var.env}"
    name = "redis-cache"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = "${data.terraform_remote_state.networking.private_subnet_ids}"
    dns_zone_id = "${data.terraform_remote_state.networking.zone_id}"

    security_groups = "${module.sg.redis_security_groups}"
    iam_instance_profile = "${module.iam.redis_instance_profile}"

    key_name = "${var.key_name}"

    instance_type = "t2.medium"
}
*/
