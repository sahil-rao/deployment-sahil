module "backoffice" {
    source = "../../services/backoffice"

    region = "${var.region}"
    env = "${var.env}"
    name = "backoffice"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    dns_zone_id = "${data.terraform_remote_state.networking.zone_id}"
    security_groups = ["${module.sg.backoffice_security_groups}"]

    instance_type = "t2.medium"
    instance_count = 1

    iam_instance_profile = "${module.iam.backoffice_instance_profile}"
    key_name = "${var.key_name}"
}
