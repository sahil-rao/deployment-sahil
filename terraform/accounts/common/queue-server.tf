module "queue-server" {
    source = "../../services/queue-server"

    region = "${var.region}"
    env = "${var.env}"
    name = "queue-server"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.private_subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"
    security_groups = ["${module.sg.queue_server_security_groups}"]

    iam_instance_profile = "${module.iam.queue_server_instance_profile}"
    key_name = "${var.key_name}"

    instance_type = "t2.micro"
    instance_count = 2
}
