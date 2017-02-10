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
