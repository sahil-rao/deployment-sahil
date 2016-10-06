module "api" {
    source = "../../services/api"

    subnet_ids = "${var.private_subnet_ids}"
    zone_id = "${var.dns_zone_id}"

    api_elb_security_groups = "${module.sg.api_elb_security_groups}"
    api_elb_dns_name = "${var.api_elb_dns_name}"
    api_elb_internal = "${var.api_elb_internal}"

    backoffice_instance_ids = "${module.backoffice.instance_ids}"
}
