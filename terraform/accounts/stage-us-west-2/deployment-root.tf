module "deployment-root" {
    source = "../../services/deployment-root"

    region = "${var.region}"
    env = "${var.env}"
    name = "deployment-root"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = ["${data.terraform_remote_state.networking.public_subnet_ids}"]
    public_cidr = "${module.cloudera-exit-cidr.cidr}"
    dns_zone_id = "${data.terraform_remote_state.networking.zone_id}"
    security_groups = ["${module.sg.deployment_root_security_groups}"]

    instance_type = "t2.micro"
    instance_count = 1

    key_name = "${var.key_name}"
}
