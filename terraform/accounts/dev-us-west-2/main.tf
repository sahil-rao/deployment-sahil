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

module "common" {
    source = "../common"

    env = "${var.env}"
    
    # Networking
    region = "${var.region}"
    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    private_cidrs = [
        "${data.terraform_remote_state.networking.all_access_cidrs}",
    ]
    public_cidrs = [
        "${data.terraform_remote_state.networking.all_access_cidrs}",
    ]
    private_subnet_ids = [
        "${data.terraform_remote_state.networking.private_subnet_ids}",
    ]
    public_subnet_ids = [
        "${data.terraform_remote_state.networking.private_subnet_ids}",
    ]

    dns_zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    dns_zone_name = "${data.terraform_remote_state.networking.zone_name}"

    # Instances
    key_name = "${var.key_name}"
    instance_managed_policies = ["${data.terraform_remote_state.networking.instance_managed_policies}"]
    # FIXME: This might be removable in 0.9.x
    # Unfortunately due to https://github.com/hashicorp/terraform/pull/10418,
    # we can't actually pass or compute the count from a data source.
    num_instance_managed_policies = "2"

    backoffice_instance_type = "t2.large"
    backoffice_instance_count = 8

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"

    logging_elasticsearch_version = "v005"
    logging_elasticsearch_ami = "ami-23d00643"

    logging_redis_version = "v005"
    logging_redis_ami = "ami-4bdf092b"

    redis_cache_version = "v005"
    redis_cache_ami = "ami-4bdf092b"

    # Datadog
    datadog_api_key = "${var.datadog_api_key}"

    s3_redis_backups_expiration_days = "${var.s3_redis_backups_expiration_days}"

    account_tls_cert_arn = "${data.terraform_remote_state.networking.account_tls_cert_arn}"

    nodejs_elb_internal = true
}
