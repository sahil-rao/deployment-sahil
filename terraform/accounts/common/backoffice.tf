module "backoffice" {
    source = "../../services/backoffice"

    region = "${var.region}"
    env = "${var.env}"
    name = "backoffice"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.private_subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"
    security_groups = ["${module.sg.backoffice_security_groups}"]

    instance_type = "${var.backoffice_instance_type}"
    instance_count = "${var.backoffice_instance_count}"

    iam_instance_profile = "${module.iam.backoffice_instance_profile}"
    key_name = "${var.key_name}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}
