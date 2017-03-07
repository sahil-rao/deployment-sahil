module "load-balancer" {
    source = "../../services/load-balancer"

    region = "${var.region}"
    env = "${var.env}"
    name = "load-balancer"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"

    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.all_access_cidrs}",
        "${data.terraform_remote_state.networking.vpc_cidr}",
    ]
    public_cidrs = [
        "${data.terraform_remote_state.networking.all_access_cidrs}",
        "${data.terraform_remote_state.networking.allowed_admin_internet_cidrs}",
    ]

    instance_managed_policies = ["${data.terraform_remote_state.networking.instance_managed_policies}"]
    # FIXME: This might be removable in 0.9.x
    # Unfortunately due to https://github.com/hashicorp/terraform/pull/10418,
    # we can't actually pass or compute the count from a data source.
    num_instance_managed_policies = "2"

    instance_type = "t2.micro"
    instance_count = 1

    key_name = "${var.key_name}"
}

resource "aws_eip" "default" {
  instance = "${module.load-balancer.instance_id}"
  vpc      = true
}

resource "aws_route53_record" "api" {
    count = "2"
    zone_id = "${element(list(data.terraform_remote_state.networking.private_zone_id,
                              data.terraform_remote_state.networking.public_zone_id), count.index)}"
    name = "www2"
    type = "A"
    ttl = "300"

    records = ["${aws_eip.default.private_ip}"]
}
