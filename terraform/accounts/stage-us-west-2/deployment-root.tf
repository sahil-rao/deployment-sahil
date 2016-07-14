module "deployment-root" {
    source = "../../services/deployment-root"

    region = "${var.region}"
    env = "${var.env}"
    name = "deployment-root"

    vpc_id = "${terraform_remote_state.networking.output.vpc_id}"
    vpc_cidr = "${terraform_remote_state.networking.output.vpc_cidr}"
    subnet_ids = "${terraform_remote_state.networking.output.public_subnet_ids}"
    public_cidr = "${module.cloudera-exit-cidr.cidr}"

    instance_type = "t2.micro"
    instance_count = 1

    key_name = "${var.key_name}"
}
