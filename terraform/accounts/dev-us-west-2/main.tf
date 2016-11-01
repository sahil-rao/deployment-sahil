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

module "cloudera-exit-cidr" {
    source = "../../modules/cloudera-exit-cidr"
}

module "common" {
    source = "../common"

    env = "${var.env}"
    
    # Networking
    region = "${var.region}"
    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    private_cidrs = [
        "${var.all_access_cidrs}",
    ]
    public_cidrs = [
        "${var.all_access_cidrs}",
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

    api_elb_dns_name = "navoptapi"
    api_elb_internal = "true"

    logging_elasticsearch_version = "v1"
    logging_elasticsearch_ami = "ami-23d00643"

    logging_redis_version = "v1"
    logging_redis_ami = "ami-4bdf092b"

    redis_cache_version = "v1"
    redis_cache_ami = "ami-4bdf092b"

    # Datadog
    datadog_api_key = "${var.datadog_api_key}"

    s3_redis_backups_expiration_days = 7
}

resource "aws_route53_record" "website" {
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    name = ""
    type = "A"
    ttl = "5"
    records = ["${module.common.nginx_private_eip}"]
}
