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
        "${data.terraform_remote_state.networking.vpc_cidr}"
    ]
    public_cidrs = [
        "${data.terraform_remote_state.networking.allowed_internet_cidrs}",
    ]
    private_subnet_ids = [
        "${data.terraform_remote_state.networking.private_subnet_ids}",
    ]
    public_subnet_ids = [
        "${data.terraform_remote_state.networking.public_subnet_ids}",
    ]

    dns_zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    dns_zone_name = "${data.terraform_remote_state.networking.zone_name}"

    # Instances
    key_name = "${var.key_name}"

    backoffice_instance_type = "t2.micro"
    backoffice_instance_count = 1

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"

    logging_elasticsearch_version = "v023"
    logging_elasticsearch_ami = "ami-062efa66"
    logging_elasticsearch_instance_type = "t2.micro"

    logging_redis_version = "v023"
    logging_redis_ami = "ami-ec21f58c"

    redis_cache_version = "v023"
    redis_cache_ami = "ami-ec21f58c"
    redis_cache_instance_type = "t2.micro"

    # Datadog
    datadog_api_key = "${var.datadog_api_key}"

    s3_redis_backups_expiration_days = "${var.s3_redis_backups_expiration_days}"

    account_tls_cert_arn = "${data.terraform_remote_state.networking.account_tls_cert_arn}"

    nodejs_elb_internal = false
}

resource "aws_route53_record" "private_website" {
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    name = ""
    type = "A"
    ttl = "5"
    records = ["${module.common.nginx_private_eip}"]
}

resource "aws_route53_record" "public_website" {
    zone_id = "${data.terraform_remote_state.networking.public_zone_id}"
    name = ""
    type = "A"
    ttl = "5"
    records = ["${module.common.nginx_public_eip}"]
}
