module "redis-cache" {
    source = "../../services/redis"

    name = "redis-cache"
    key_name = "${var.key_name}"
    iam_instance_profile = "${module.iam.redis_instance_profile}"

    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    security_groups = "${module.sg.redis_security_groups}"
    zone_name = "${data.terraform_remote_state.networking.dns_zone_name}"

    version = "v1"
    ami_id = "ami-4bdf092b"
    instance_type = "t2.micro" # "r3.2xlarge"
    ebs_optimized = false
    min_size = 0
    max_size = 1
    desired_capacity = 1
    quorum_size = 1

    env = "${var.cluster_name}"
    service = "redis-cache"
    datadog_api_key = "${var.datadog_api_key}"
}
