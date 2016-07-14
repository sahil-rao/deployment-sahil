provider "aws" {
    profile = "${var.profile}"
    region = "${var.region}"
}

resource "terraform_remote_state" "networking" {
    backend = "s3"
    config {
        profile = "${var.profile}"
        bucket = "${var.terraform_remote_state_bucket}"
        region = "${var.terraform_remote_state_region}"
        key = "${var.terraform_remote_state_key}"
    }
}

module "cloudera-exit-cidr" {
    source = "../../modules/cloudera-exit-cidr"
}

module "admin" {
    source = "../../services/admin"

    region = "${var.region}"
    env = "stage"
    name = "admin"

    vpc_id = "${terraform_remote_state.networking.output.vpc_id}"
    vpc_cidr = "${terraform_remote_state.networking.output.vpc_cidr}"
    subnet_ids = "${terraform_remote_state.networking.output.public_subnet_ids}"

    public_cidr = "${module.cloudera-exit-cidr.cidr}"

    key_name = "${var.key_name}"
}
