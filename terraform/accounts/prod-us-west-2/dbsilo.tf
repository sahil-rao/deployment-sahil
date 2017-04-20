module "dbsilo1-mongodb" {
    source = "../../services/mongodb-asg"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.vpc_cidr}",
        "${var.old_vpc_cidr}",
    ]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    service = "dbsilo1-mongo"
    env = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    name = "${var.cluster_name}-dbsilo1-mongo"
    replica_set = "dbsilo1"
    version = "v028"
    ami_id = "ami-a82bafc8" # mongo 3.4
    instance_type = "m4.xlarge"
    min_size = 0
    max_size = 3
    desired_capacity = 3
    ebs_optimized = false

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}

module "dbsilo2-mongodb" {
    source = "../../services/mongodb-asg"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.vpc_cidr}",
        "${var.old_vpc_cidr}",
    ]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    service = "dbsilo2-mongo"
    env = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    name = "${var.cluster_name}-dbsilo2-mongo"
    replica_set = "dbsilo2"
    version = "v028"
    ami_id = "ami-a82bafc8" # mongo 3.4
    instance_type = "m4.xlarge"
    min_size = 0
    max_size = 3
    desired_capacity = 3
    ebs_optimized = false

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}

module "dbsilo3-mongodb" {
    source = "../../services/mongodb-asg"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]
    private_cidrs = [
        "${data.terraform_remote_state.networking.vpc_cidr}",
        "${var.old_vpc_cidr}",
    ]
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    zone_name = "${data.terraform_remote_state.networking.zone_name}"

    key_name = "${var.key_name}"

    service = "dbsilo3-mongo"
    env = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    name = "${var.cluster_name}-dbsilo3-mongo"
    replica_set = "dbsilo3"
    version = "v028"
    ami_id = "ami-a82bafc8" # mongo 3.4
    instance_type = "m4.xlarge"
    min_size = 0
    max_size = 3
    desired_capacity = 3
    ebs_optimized = true

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${module.log-service.destination_arn}"
}

# FIXME: Temporary CNAME until we transition redis to the new VPC
resource "aws_route53_record" "dbsilo1-redis-master-xplain" {
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    name = "dbsilo1-redis-master"
    type = "CNAME"
    ttl = "5"
    records = ["redismaster.dbsilo1.app.xplain.io"]
}

# FIXME: Temporary CNAME until we transition redis to the new VPC
resource "aws_route53_record" "dbsilo1-redis-master" {
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    name = "redismaster.dbsilo1"
    type = "CNAME"
    ttl = "5"
    records = ["redismaster.dbsilo1.app.xplain.io"]
}

# FIXME: Temporary CNAME until we transition redis to the new VPC
resource "aws_route53_record" "dbsilo2-redis-master-xplain" {
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    name = "dbsilo2-redis-master"
    type = "CNAME"
    ttl = "5"
    records = ["redismaster.dbsilo2.app.xplain.io"]
}

# FIXME: Temporary CNAME until we transition redis to the new VPC
resource "aws_route53_record" "dbsilo2-redis-master" {
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    name = "redismaster.dbsilo2"
    type = "CNAME"
    ttl = "5"
    records = ["redismaster.dbsilo2.app.xplain.io"]
}

# FIXME: Temporary CNAME until we transition redis to the new VPC
resource "aws_route53_record" "dbsilo3-redis-master-xplain" {
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    name = "dbsilo3-redis-master"
    type = "CNAME"
    ttl = "5"
    records = ["redismaster.dbsilo3.app.xplain.io"]
}

# FIXME: Temporary CNAME until we transition redis to the new VPC
resource "aws_route53_record" "dbsilo3-redis-master" {
    zone_id = "${data.terraform_remote_state.networking.private_zone_id}"
    name = "redismaster.dbsilo3"
    type = "CNAME"
    ttl = "5"
    records = ["redismaster.dbsilo3.app.xplain.io"]
}

module "s3" {
    source = "../../services/s3"

    env = "${var.env}"
    navopt_name = "navopt-${var.env}"
    backups_name = "navopt-backups-${var.env}"

    redis_expiration_days = "${var.s3_redis_backups_expiration_days}"
}
