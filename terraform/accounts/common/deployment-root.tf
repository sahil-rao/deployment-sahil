module "deployment-root" {
    source = "../../services/deployment-root"

    region = "${var.region}"
    env = "${var.env}"
    name = "deployment-root"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.public_subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"
    security_groups = ["${module.sg.deployment_root_security_groups}"]

    instance_type = "t2.micro"
    instance_count = 1

    key_name = "${var.key_name}"
}
