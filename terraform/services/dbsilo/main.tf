variable "vpc_id" {}
variable "subnet_ids" {
    type = "list"
}
variable "zone_name" {}

variable "dbsilo_name" {}
variable "cluster_name" {}
variable "datadog_api_key" {}

variable "key_name" {}

###################################################################

variable "mongo_name" {}
variable "mongo_replica_set" {
    default = ""
}
variable "mongo_security_groups" {
    type = "list"
}
variable "mongo_iam_instance_profile" {}

variable "mongo_version" {}
variable "mongo_ami_id" {}
variable "mongo_instance_type" {}
variable "mongo_min_size" {}
variable "mongo_max_size" {}
variable "mongo_desired_capacity" {}
variable "mongo_snapshot_id" {
    default = "null"
}
variable "mongo_ebs_optimized" {
    default = true
}

###################################################################

variable "redis_name" {}
variable "redis_security_groups" {
    type = "list"
}
variable "redis_iam_instance_profile" {}

variable "redis_version" {}
variable "redis_ami_id" {}
variable "redis_instance_type" {}
variable "redis_min_size" {}
variable "redis_max_size" {}
variable "redis_desired_capacity" {}
variable "redis_backup_file" {
    default = ""
}
variable "redis_quorum_size" {}
variable "redis_ebs_optimized" {
    default = true
}
variable "redis_backups_enabled" {
    default = "true"
}

###################################################################

variable "elasticsearch_name" {}
variable "elasticsearch_security_groups" {
    type = "list"
}
variable "elasticsearch_iam_instance_profile" {}

variable "elasticsearch_version" {}
variable "elasticsearch_ami_id" {}
variable "elasticsearch_instance_type" {}
variable "elasticsearch_min_size" {}
variable "elasticsearch_max_size" {}
variable "elasticsearch_desired_capacity" {}
variable "elasticsearch_ebs_optimized" {
    default = true
}

variable "cloudwatch_retention_in_days" {}
variable "log_subscription_destination_arn" {}

###################################################################

module "mongodb" {
    source = "../mongodb-asg"

    subnet_ids = ["${var.subnet_ids}"]
    zone_name = "${var.zone_name}"
    security_groups = ["${var.mongo_security_groups}"]

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.mongo_iam_instance_profile}"

    name = "${var.mongo_name}"
    version = "${var.mongo_version}"
    replica_set = "${var.mongo_replica_set}"
    env = "${var.cluster_name}"
    service = "${var.dbsilo_name}-mongo"
    datadog_api_key = "${var.datadog_api_key}"
    snapshot_id = "${var.mongo_snapshot_id}"

    ami_id = "${var.mongo_ami_id}"
    instance_type = "${var.mongo_instance_type}"
    min_size = "${var.mongo_min_size}"
    max_size = "${var.mongo_max_size}"
    desired_capacity = "${var.mongo_desired_capacity}"
    ebs_optimized = "${var.mongo_ebs_optimized}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "redis" {
    source = "../redis-asg"

    subnet_ids = ["${var.subnet_ids}"]
    zone_name = "${var.zone_name}"
    security_groups = ["${var.redis_security_groups}"]

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.redis_iam_instance_profile}"

    name = "${var.redis_name}"
    version = "${var.redis_version}"
    env = "${var.cluster_name}"
    service = "${var.dbsilo_name}-redis"
    datadog_api_key = "${var.datadog_api_key}"
    backup_file = "${var.redis_backup_file}"
    quorum_size = "${var.redis_quorum_size}"

    ami_id = "${var.redis_ami_id}"
    instance_type = "${var.redis_instance_type}"
    min_size = "${var.redis_min_size}"
    max_size = "${var.redis_max_size}"
    desired_capacity = "${var.redis_desired_capacity}"
    ebs_optimized = "${var.redis_ebs_optimized}"
    backups_enabled = "${var.redis_backups_enabled}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "elasticsearch" {
    source = "../elasticsearch-asg"

    subnet_ids = ["${var.subnet_ids}"]
    zone_name = "${var.zone_name}"
    security_groups = ["${var.elasticsearch_security_groups}"]

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.elasticsearch_iam_instance_profile}"

    name = "${var.elasticsearch_name}"
    version = "${var.elasticsearch_version}"
    env = "${var.cluster_name}"
    service = "${var.dbsilo_name}-elasticsearch"
    datadog_api_key = "${var.datadog_api_key}"

    ami_id = "${var.elasticsearch_ami_id}"
    instance_type = "${var.elasticsearch_instance_type}"
    min_size = "${var.elasticsearch_min_size}"
    max_size = "${var.elasticsearch_max_size}"
    desired_capacity = "${var.elasticsearch_desired_capacity}"
    ebs_optimized = "${var.elasticsearch_ebs_optimized}"

    cloudwatch_retention_in_days = "${var.cloudwatch_retention_in_days}"
    log_subscription_destination_arn = "${var.log_subscription_destination_arn}"
}
