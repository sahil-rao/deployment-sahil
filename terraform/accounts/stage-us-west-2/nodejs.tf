module "nodejs" {
    source = "../../services/nodejs"

    region = "${var.region}"
    env = "${var.env}"
    name = "nodejs"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    dns_zone_id = "${data.terraform_remote_state.networking.dns_zone_id}"
    security_groups = ["${module.sg.nodejs_security_groups}"]

    key_name = "${var.key_name}"

    iam_instance_profile = "${module.iam.nodejs_instance_profile}"
    instance_type = "t2.micro"
}
