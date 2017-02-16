module "load-balancer" {
    source = "../../services/load-balancer"

    region = "${var.region}"
    env = "${var.env}"
    name = "load-balancer"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"

    subnet_ids = ["${data.terraform_remote_state.networking.public_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.vpc_cidr}",
        "${var.old_vpc_cidr}",
    ]
    public_cidrs = [
        "0.0.0.0/0",
    ]

    instance_type = "m3.medium"
    instance_count = 1

    key_name = "${var.key_name}"
}

resource "aws_eip" "frontend" {
  instance = "${module.load-balancer.instance_id}"
  vpc      = true
}

resource "aws_route53_record" "frontend" {
    count = "2"
    zone_id = "${element(list(data.terraform_remote_state.networking.private_zone_id,
                              data.terraform_remote_state.networking.public_zone_id), count.index)}"
    name = "${data.terraform_remote_state.networking.zone_name}"
    type = "A"
    ttl = "300"

    records = ["${aws_eip.frontend.public_ip}"]
}

resource "aws_eip" "admin" {
  instance = "i-73fb34ae"
  vpc      = true
}

resource "aws_route53_record" "admin" {
    count = "2"
    zone_id = "${element(list(data.terraform_remote_state.networking.private_zone_id,
                              data.terraform_remote_state.networking.public_zone_id), count.index)}"
    name = "app-dashboard"
    type = "A"
    ttl = "300"

    records = ["${aws_eip.admin.public_ip}"]
}
