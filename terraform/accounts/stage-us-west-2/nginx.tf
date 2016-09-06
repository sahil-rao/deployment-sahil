module "nginx" {
    source = "../../services/nginx"

    region = "${var.region}"
    env = "${var.env}"
    name = "nginx"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = ["${data.terraform_remote_state.networking.public_subnet_ids}"]
    public_cidr = "${module.cloudera-exit-cidr.cidr}"
    dns_zone_id = "${data.terraform_remote_state.networking.dns_zone_id}"
    security_groups = ["${module.sg.nginx_security_groups}"]

    instance_type = "t2.micro"
    instance_count = 1

    iam_instance_profile = "${module.iam.nginx_instance_profile}"
    key_name = "${var.key_name}"
}
