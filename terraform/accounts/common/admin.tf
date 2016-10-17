module "admin" {
    source = "../../services/admin"

    region = "${var.region}"
    env = "${var.env}"
    name = "admin"

    vpc_id = "${var.vpc_id}"
    subnet_ids = [
        "${var.public_subnet_ids}"
    ]
    dns_zone_id = "${var.dns_zone_id}"
    security_groups = ["${module.sg.admin_security_groups}"]

    instance_type = "t2.micro"

    iam_instance_profile = "${module.iam.admin_instance_profile}"
    key_name = "${var.key_name}"
}
