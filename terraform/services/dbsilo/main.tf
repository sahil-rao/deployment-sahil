variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}

variable "dbsilo_name" {}
variable "cluster_name" {}
variable "datadog_api_key" {}

variable "key_name" {}

###################################################################

variable "mongo_name" {}
variable "mongo_security_groups" {}
variable "mongo_iam_instance_profile" {}

variable "mongo_blue_version" {}
variable "mongo_blue_ami_id" {}
variable "mongo_blue_instance_type" {}
variable "mongo_blue_min_size" {}
variable "mongo_blue_max_size" {}
variable "mongo_blue_desired_capacity" {}
variable "mongo_blue_snapshot_id" {
    default = "null"
}
variable "mongo_blue_ebs_optimized" {
    default = true
}

variable "mongo_green_version" {}
variable "mongo_green_ami_id" {}
variable "mongo_green_instance_type" {}
variable "mongo_green_min_size" {}
variable "mongo_green_max_size" {}
variable "mongo_green_desired_capacity" {}
variable "mongo_green_snapshot_id" {
    default = "null"
}
variable "mongo_green_ebs_optimized" {
    default = true
}

###################################################################

variable "redis_name" {}
variable "redis_security_groups" {}
variable "redis_iam_instance_profile" {}

variable "redis_blue_version" {}
variable "redis_blue_ami_id" {}
variable "redis_blue_instance_type" {}
variable "redis_blue_min_size" {}
variable "redis_blue_max_size" {}
variable "redis_blue_desired_capacity" {}
variable "redis_blue_backup_file" {
    default = ""
}
variable "redis_blue_ebs_optimized" {
    default = true
}


variable "redis_green_version" {}
variable "redis_green_ami_id" {}
variable "redis_green_instance_type" {}
variable "redis_green_min_size" {}
variable "redis_green_max_size" {}
variable "redis_green_desired_capacity" {}
variable "redis_green_backup_file" {
    default = ""
}
variable "redis_green_ebs_optimized" {
    default = true
}

###################################################################

variable "elasticsearch_name" {}
variable "elasticsearch_security_groups" {}
variable "elasticsearch_iam_instance_profile" {}

variable "elasticsearch_blue_version" {}
variable "elasticsearch_blue_ami_id" {}
variable "elasticsearch_blue_instance_type" {}
variable "elasticsearch_blue_min_size" {}
variable "elasticsearch_blue_max_size" {}
variable "elasticsearch_blue_desired_capacity" {}
variable "elasticsearch_blue_ebs_optimized" {
    default = true
}

variable "elasticsearch_green_version" {}
variable "elasticsearch_green_ami_id" {}
variable "elasticsearch_green_instance_type" {}
variable "elasticsearch_green_min_size" {}
variable "elasticsearch_green_max_size" {}
variable "elasticsearch_green_desired_capacity" {}
variable "elasticsearch_green_ebs_optimized" {
    default = true
}

###################################################################

module "mongodb-blue" {
    source = "../mongodb-asg"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${var.mongo_security_groups}"

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.mongo_iam_instance_profile}"

    name = "${var.mongo_name}"
    version = "blue-${var.mongo_blue_version}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"
    snapshot_id = "${var.mongo_blue_snapshot_id}"

    ami_id = "${var.mongo_blue_ami_id}"
    instance_type = "${var.mongo_blue_instance_type}"
    min_size = "${var.mongo_blue_min_size}"
    max_size = "${var.mongo_blue_max_size}"
    desired_capacity = "${var.mongo_blue_desired_capacity}"
    ebs_optimized = "${var.mongo_blue_ebs_optimized}"
}

module "mongodb-green" {
    source = "../mongodb-asg"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${var.mongo_security_groups}"

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.mongo_iam_instance_profile}"

    name = "${var.mongo_name}"
    version = "green-${var.mongo_green_version}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"
    snapshot_id = "${var.mongo_green_snapshot_id}"

    ami_id = "${var.mongo_green_ami_id}"
    instance_type = "${var.mongo_green_instance_type}"
    min_size = "${var.mongo_green_min_size}"
    max_size = "${var.mongo_green_max_size}"
    desired_capacity = "${var.mongo_green_desired_capacity}"
    ebs_optimized = "${var.mongo_green_ebs_optimized}"
}

module "redis-blue" {
    source = "../redis-asg"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${var.redis_security_groups}"

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.redis_iam_instance_profile}"

    name = "${var.redis_name}"
    version = "blue-${var.redis_blue_version}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"
    backup_file = "${var.redis_blue_backup_file}"

    ami_id = "${var.redis_blue_ami_id}"
    instance_type = "${var.redis_blue_instance_type}"
    min_size = "${var.redis_blue_min_size}"
    max_size = "${var.redis_blue_max_size}"
    desired_capacity = "${var.redis_blue_desired_capacity}"
    ebs_optimized = "${var.redis_blue_ebs_optimized}"
}

module "redis-green" {
    source = "../redis-asg"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${var.redis_security_groups}"

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.redis_iam_instance_profile}"

    name = "${var.redis_name}"
    version = "green-${var.redis_green_version}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"
    backup_file = "${var.redis_green_backup_file}"

    ami_id = "${var.redis_green_ami_id}"
    instance_type = "${var.redis_green_instance_type}"
    min_size = "${var.redis_green_min_size}"
    max_size = "${var.redis_green_max_size}"
    desired_capacity = "${var.redis_green_desired_capacity}"
    ebs_optimized = "${var.redis_green_ebs_optimized}"
}

module "elasticsearch-blue" {
    source = "../elasticsearch-asg"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${var.elasticsearch_security_groups}"

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.elasticsearch_iam_instance_profile}"

    name = "${var.elasticsearch_name}"
    version = "blue-${var.elasticsearch_blue_version}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    ami_id = "${var.elasticsearch_blue_ami_id}"
    instance_type = "${var.elasticsearch_blue_instance_type}"
    min_size = "${var.elasticsearch_blue_min_size}"
    max_size = "${var.elasticsearch_blue_max_size}"
    desired_capacity = "${var.elasticsearch_blue_desired_capacity}"
    ebs_optimized = "${var.elasticsearch_blue_ebs_optimized}"
}

module "elasticsearch-green" {
    source = "../elasticsearch-asg"

    subnet_ids = "${var.subnet_ids}"
    security_groups = "${var.elasticsearch_security_groups}"

    key_name = "${var.key_name}"
    iam_instance_profile = "${var.elasticsearch_iam_instance_profile}"

    name = "${var.elasticsearch_name}"
    version = "green-${var.elasticsearch_green_version}"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    ami_id = "${var.elasticsearch_green_ami_id}"
    instance_type = "${var.elasticsearch_green_instance_type}"
    min_size = "${var.elasticsearch_green_min_size}"
    max_size = "${var.elasticsearch_green_max_size}"
    desired_capacity = "${var.elasticsearch_green_desired_capacity}"
    ebs_optimized = "${var.elasticsearch_green_ebs_optimized}"
}
