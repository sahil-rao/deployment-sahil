module "nodejs" {
    source = "../../services/nodejs"

    region = "${var.region}"
    env = "${var.env}"
    name = "nodejs"

    vpc_id = "${terraform_remote_state.networking.output.vpc_id}"
    vpc_cidr = "${terraform_remote_state.networking.output.vpc_cidr}"
    subnet_ids = "${terraform_remote_state.networking.output.private_subnet_ids}"
    dns_zone_id = "${terraform_remote_state.networking.output.zone_id}"
    security_groups = "${module.sg.nodejs_security_groups}"

    key_name = "${var.key_name}"

    iam_instance_profile = "${module.iam.nodejs_instance_profile}"
    instance_type = "t2.micro"
}
