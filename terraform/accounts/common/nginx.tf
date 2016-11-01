module "nginx" {
    source = "../../services/nginx"

    region = "${var.region}"
    env = "${var.env}"
    name = "nginx"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.public_subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"
    security_groups = ["${module.sg.nginx_security_groups}"]

    instance_type = "t2.micro"
    instance_count = 1

    iam_instance_profile = "${module.iam.nginx_instance_profile}"
    key_name = "${var.key_name}"
}
