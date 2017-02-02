module "nodejs" {
    source = "../../services/nodejs"

    region = "${var.region}"
    env = "${var.env}"
    name = "nodejs"

    vpc_id = "${var.vpc_id}"
    subnet_ids = ["${var.private_subnet_ids}"]
    public_subnet_ids = ["${var.public_subnet_ids}"]
    dns_zone_id = "${var.dns_zone_id}"
    security_groups = ["${module.sg.nodejs_security_groups}"]
    nodejs_elb_security_groups = ["${module.sg.nodejs_elb_security_groups}"]
    key_name = "${var.key_name}"

    iam_instance_profile = "${module.iam.nodejs_instance_profile}"
    instance_type = "t2.large"
    instance_count = 2
    
    navopt_elb_cert_arn = "${var.account_tls_cert_arn}"
    nodejs_elb_internal = "${var.nodejs_elb_internal}"
}
