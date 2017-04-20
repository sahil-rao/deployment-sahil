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

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.vpc_cidr}",
        "${var.old_vpc_cidr}",
    ]
    dns_zone_id = "${data.terraform_remote_state.networking.private_zone_id}"

    instance_type = "c3.xlarge"
    instance_count = 1

    key_name = "${var.key_name}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"

    s3_navopt_bucket_arn = "${module.s3.navopt_arn}"
}
