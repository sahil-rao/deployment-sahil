terraform {
    backend "s3" {
        bucket = "cloudera-terraform-infrastructure"
        key = "prod/navopt-us-west-2-prod/external/terraform.tfstate"
        region = "us-west-2"
        profile = "navopt_prod"
    }
}

provider "aws" {
    profile = "${var.profile}"
    region = "${var.region}"
}

data "terraform_remote_state" "networking" {
    backend = "s3"
    config {
        profile = "${var.profile}"
        bucket = "${var.terraform_remote_state_bucket}"
        region = "${var.terraform_remote_state_region}"
        key = "${var.terraform_remote_state_key}"
    }
}

module "log-service" {
    source = "../../modules/log-service"

    environment = "${var.env}"
}
