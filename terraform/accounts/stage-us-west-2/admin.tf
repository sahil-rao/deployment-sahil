module "admin" {
    source = "../../services/admin"

    region = "${var.region}"
    env = "${var.env}"
    name = "admin"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = ["${data.terraform_remote_state.networking.public_subnet_ids}"]
    public_cidr = "${module.cloudera-exit-cidr.cidr}"
    dns_zone_id = "${data.terraform_remote_state.networking.zone_id}"
    security_groups = ["${module.sg.admin_security_groups}"]

    instance_type = "t2.micro"

    iam_instance_profile = "${module.iam.admin_instance_profile}"
    key_name = "${var.key_name}"
}
