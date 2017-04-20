module "dbsilo1-elasticsearch" {
    source = "../../services/elasticsearch-asg"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.vpc_cidr}",
        "${var.old_vpc_cidr}",
    ]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    service = "dbsilo1-elasticsearch"
    env = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    name = "${var.cluster_name}-dbsilo1-elasticsearch"
    version = "v034"
    ami_id = "ami-b258c5d2" # elasticsearch 2.4.4
    instance_type = "m3.xlarge"
    min_size = 0
    max_size = 3
    desired_capacity = 3
    ebs_optimized = true

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"

    elasticsearch_heap_size = "8g"
}
