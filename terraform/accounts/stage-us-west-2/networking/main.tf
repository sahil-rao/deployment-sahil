provider "aws" {
    profile = "navopt_stage"
    region = "${var.region}"
}

module "networking" {
    source = "../../../services/networking"

    region = "${var.region}"
    availability_zones = "${var.availability_zones}"

    vpc_name = "${var.vpc_name}"
    vpc_cidr = "${var.vpc_cidr}"

    public_subnets = "${var.public_subnets}"
    private_subnets = "${var.private_subnets}"

    virtual_gateway_id = "${var.virtual_gateway_id}"
}
