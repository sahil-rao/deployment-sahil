module "dbsilo1-mongodb" {
    source = "../../services/mongodb-asg"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = ["${data.terraform_remote_state.networking.vpc_cidr}"]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    service = "dbsilo1-mongo"
    env = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    name = "${var.cluster_name}-dbsilo1-mongo"
    replica_set = "dbsilo1"
    version = "v023"
    ami_id = "ami-0a098d6a" # mongo 3.0
    instance_type = "m4.xlarge"
    min_size = 0
    max_size = 1
    desired_capacity = 1
    ebs_optimized = false

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}

module "dbsilo2-mongodb" {
    source = "../../services/mongodb-asg"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = ["${data.terraform_remote_state.networking.vpc_cidr}"]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    service = "dbsilo2-mongo"
    env = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    name = "${var.cluster_name}-dbsilo2-mongo"
    replica_set = "dbsilo2"
    version = "v023"
    ami_id = "ami-0a098d6a" # mongo 3.0
    instance_type = "m4.xlarge"
    min_size = 0
    max_size = 1
    desired_capacity = 1
    ebs_optimized = false

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}

module "dbsilo3-mongodb" {
    source = "../../services/mongodb-asg"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = ["${data.terraform_remote_state.networking.vpc_cidr}"]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    service = "dbsilo3-mongo"
    env = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    name = "${var.cluster_name}-dbsilo3-mongo"
    replica_set = "dbsilo3"
    version = "v023"
    ami_id = "ami-0a098d6a" # mongo 3.0
    instance_type = "m4.xlarge"
    min_size = 0
    max_size = 1
    desired_capacity = 1
    ebs_optimized = false

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}
