variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}

variable "name_prefix" {}
variable "dbsilo_name" {}
variable "cluster_name" {}
variable "datadog_api_key" {}

variable "key_name" {}

variable "mongo_blue_name_prefix" {}
variable "mongo_blue_ami_id" {}
variable "mongo_blue_instance_type" {}
variable "mongo_blue_min_size" {}
variable "mongo_blue_max_size" {}
variable "mongo_blue_desired_capacity" {}

variable "mongo_green_name_prefix" {}
variable "mongo_green_ami_id" {}
variable "mongo_green_instance_type" {}
variable "mongo_green_min_size" {}
variable "mongo_green_max_size" {}
variable "mongo_green_desired_capacity" {}

variable "redis_blue_name_prefix" {}
variable "redis_blue_ami_id" {}
variable "redis_blue_instance_type" {}
variable "redis_blue_min_size" {}
variable "redis_blue_max_size" {}
variable "redis_blue_desired_capacity" {}
variable "redis_blue_backup_file" {
    default = ""
}

variable "redis_green_name_prefix" {}
variable "redis_green_ami_id" {}
variable "redis_green_instance_type" {}
variable "redis_green_min_size" {}
variable "redis_green_max_size" {}
variable "redis_green_desired_capacity" {}
variable "redis_green_backup_file" {
    default = ""
}

variable "elasticsearch_blue_name_prefix" {}
variable "elasticsearch_blue_ami_id" {}
variable "elasticsearch_blue_instance_type" {}
variable "elasticsearch_blue_min_size" {}
variable "elasticsearch_blue_max_size" {}
variable "elasticsearch_blue_desired_capacity" {}

variable "elasticsearch_green_name_prefix" {}
variable "elasticsearch_green_ami_id" {}
variable "elasticsearch_green_instance_type" {}
variable "elasticsearch_green_min_size" {}
variable "elasticsearch_green_max_size" {}
variable "elasticsearch_green_desired_capacity" {}

module "mongodb-blue" {
    source = "../mongodb"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${aws_security_group.mongo.id}"

    key_name = "${var.key_name}"
    instance_profile = "${aws_iam_instance_profile.mongo.name}"

    name_prefix = "${var.mongo_blue_name_prefix}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    ami_id = "${var.mongo_blue_ami_id}"
    instance_type = "${var.mongo_green_instance_type}"
    min_size = "${var.mongo_blue_min_size}"
    max_size = "${var.mongo_blue_max_size}"
    desired_capacity = "${var.mongo_blue_desired_capacity}"
}

module "mongodb-green" {
    source = "../mongodb"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${aws_security_group.mongo.id}"

    key_name = "${var.key_name}"
    instance_profile = "${aws_iam_instance_profile.mongo.name}"

    name_prefix = "${var.mongo_green_name_prefix}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    ami_id = "${var.mongo_green_ami_id}"
    instance_type = "${var.mongo_green_instance_type}"
    min_size = "${var.mongo_green_min_size}"
    max_size = "${var.mongo_green_max_size}"
    desired_capacity = "${var.mongo_green_desired_capacity}"
}

module "redis-blue" {
    source = "../redis"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${aws_security_group.redis.id}"

    key_name = "${var.key_name}"
    instance_profile = "${aws_iam_instance_profile.redis.name}"

    name_prefix = "${var.redis_blue_name_prefix}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"
    backup_file = "${var.redis_blue_backup_file}"

    ami_id = "${var.redis_blue_ami_id}"
    instance_type = "${var.redis_blue_instance_type}"
    min_size = "${var.redis_blue_min_size}"
    max_size = "${var.redis_blue_max_size}"
    desired_capacity = "${var.redis_blue_desired_capacity}"
}

module "redis-green" {
    source = "../redis"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${aws_security_group.redis.id}"

    key_name = "${var.key_name}"
    instance_profile = "${aws_iam_instance_profile.redis.name}"

    name_prefix = "${var.redis_green_name_prefix}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"
    backup_file = "${var.redis_green_backup_file}"

    ami_id = "${var.redis_green_ami_id}"
    instance_type = "${var.redis_green_instance_type}"
    min_size = "${var.redis_green_min_size}"
    max_size = "${var.redis_green_max_size}"
    desired_capacity = "${var.redis_green_desired_capacity}"
}

module "elasticsearch-blue" {
    source = "../elasticsearch"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${aws_security_group.elasticsearch.id}"

    key_name = "${var.key_name}"
    instance_profile = "${aws_iam_instance_profile.elasticsearch.name}"

    name_prefix = "${var.elasticsearch_blue_name_prefix}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    ami_id = "${var.elasticsearch_blue_ami_id}"
    instance_type = "${var.elasticsearch_blue_instance_type}"
    min_size = "${var.elasticsearch_blue_min_size}"
    max_size = "${var.elasticsearch_blue_max_size}"
    desired_capacity = "${var.elasticsearch_blue_desired_capacity}"
}

module "elasticsearch-green" {
    source = "../elasticsearch"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${aws_security_group.elasticsearch.id}"

    key_name = "${var.key_name}"
    instance_profile = "${aws_iam_instance_profile.elasticsearch.name}"

    name_prefix = "${var.elasticsearch_green_name_prefix}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    ami_id = "${var.elasticsearch_green_ami_id}"
    instance_type = "${var.elasticsearch_green_instance_type}"
    min_size = "${var.elasticsearch_green_min_size}"
    max_size = "${var.elasticsearch_green_max_size}"
    desired_capacity = "${var.elasticsearch_green_desired_capacity}"
}
