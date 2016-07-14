module "nginx" {
    source = "../../services/nginx"

    region = "${var.region}"
    env = "${var.env}"
    name = "nginx"

    vpc_id = "${terraform_remote_state.networking.output.vpc_id}"
    vpc_cidr = "${terraform_remote_state.networking.output.vpc_cidr}"
    subnet_ids = "${terraform_remote_state.networking.output.public_subnet_ids}"
    public_cidr = "${module.cloudera-exit-cidr.cidr}"

    key_name = "${var.key_name}"
}
