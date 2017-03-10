module "backoffice" {
    source = "../../services/backoffice"

    region = "${var.region}"
    env = "${var.env}"
    name = "backoffice"

    iam_role_name = "backoffice"
    sg_name = "backoffice"

    api_backend_dns_name = "api-backend"
    api_backend_elb_name = "api-backend-elb"
    api_backend_elb_sg_name = "api-backend-elb"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.private_subnet_ids}"]
    private_cidrs = ["${var.private_cidrs}"]
    dns_zone_id = "${var.dns_zone_id}"

    instance_type = "${var.backoffice_instance_type}"
    instance_count = "${var.backoffice_instance_count}"

    key_name = "${var.key_name}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"

    s3_navopt_bucket_arn = "${module.s3.navopt_arn}"
}
