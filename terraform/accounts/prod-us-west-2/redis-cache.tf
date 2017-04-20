module "redis-cache" {
    source = "../../services/redis-asg"

    name = "redis-cache"
    key_name = "${var.key_name}"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    private_cidrs = [
        "${data.terraform_remote_state.networking.vpc_cidr}",
        "${var.old_vpc_cidr}",
    ]
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    version = "001"
    ami_id = "ami-f8128198"
    instance_type = "m3.medium"
    ebs_optimized = false
    min_size = 1
    max_size = 1
    desired_capacity = 1
    quorum_size = 1

    env = "${var.env}"
    service = "redis-cache"
    datadog_api_key = "${var.datadog_api_key}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}
