module "backoffice" {
    source = "../../services/backoffice"

    region = "${var.region}"
    env = "${var.env}"
    name = "backoffice"

    vpc_id = "${terraform_remote_state.networking.output.vpc_id}"
    vpc_cidr = "${terraform_remote_state.networking.output.vpc_cidr}"
    subnet_ids = "${terraform_remote_state.networking.output.private_subnet_ids}"
    dns_zone_id = "${terraform_remote_state.networking.output.zone_id}"
    security_groups = "${module.sg.backoffice_security_groups}"

    instance_type = "t2.micro"
    instance_count = 1

    iam_instance_profile = "${module.iam.backoffice_instance_profile}"
    key_name = "${var.key_name}"
}
