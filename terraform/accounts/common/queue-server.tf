module "queue-server" {
    source = "../../services/queue-server"

    region = "${var.region}"
    env = "${var.env}"
    name = "queue-server"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.private_subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"
    security_groups = ["${module.sg.queue_server_security_groups}"]

    key_name = "${var.key_name}"

    instance_managed_policies = ["${var.instance_managed_policies}"]
    num_instance_managed_policies = "${var.num_instance_managed_policies}"

    instance_type = "t2.large"
    instance_count = 2

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}
