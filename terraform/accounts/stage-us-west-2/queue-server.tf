module "queue-server" {
    source = "../../services/queue-server"

    region = "${var.region}"
    env = "${var.env}"
    name = "queue-server"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    dns_zone_id = "${data.terraform_remote_state.networking.zone_id}"
    security_groups = ["${module.sg.queue_server_security_groups}"]

    iam_instance_profile = "${module.iam.queue_server_instance_profile}"
    key_name = "${var.key_name}"

    instance_type = "t2.micro"
    instance_count = 2
}
