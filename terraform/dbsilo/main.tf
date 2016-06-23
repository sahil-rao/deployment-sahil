variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}

variable "name_prefix" {}
variable "dbsilo_name" {}
variable "cluster_name" {}

variable "key_name" {}

variable "mongo_blue_ami_id" {}
variable "mongo_blue_instance_type" {}
variable "mongo_blue_min_size" {}
variable "mongo_blue_max_size" {}
variable "mongo_blue_desired_capacity" {}

variable "mongo_green_ami_id" {}
variable "mongo_green_instance_type" {}
variable "mongo_green_min_size" {}
variable "mongo_green_max_size" {}
variable "mongo_green_desired_capacity" {}

variable "redis_blue_ami_id" {}
variable "redis_blue_instance_type" {}
variable "redis_blue_min_size" {}
variable "redis_blue_max_size" {}
variable "redis_blue_desired_capacity" {}

variable "redis_green_ami_id" {}
variable "redis_green_instance_type" {}
variable "redis_green_min_size" {}
variable "redis_green_max_size" {}
variable "redis_green_desired_capacity" {}

module "mongodb-blue" {
    source = "../mongodb"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.name_prefix}-mongo-blue"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"

    ami_id = "${var.mongo_blue_ami_id}"
    instance_type = "${var.mongo_green_instance_type}"
    min_size = "${var.mongo_blue_min_size}"
    max_size = "${var.mongo_blue_max_size}"
    desired_capacity = "${var.mongo_blue_desired_capacity}"
}

module "mongodb-green" {
    source = "../mongodb"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.name_prefix}-mongo-green"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"

    ami_id = "${var.mongo_green_ami_id}"
    instance_type = "${var.mongo_green_instance_type}"
    min_size = "${var.mongo_green_min_size}"
    max_size = "${var.mongo_green_max_size}"
    desired_capacity = "${var.mongo_green_desired_capacity}"
}

module "redis-blue" {
    source = "../redis"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.name_prefix}-redis-blue"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"

    ami_id = "${var.redis_blue_ami_id}"
    instance_type = "${var.redis_blue_instance_type}"
    min_size = "${var.redis_blue_min_size}"
    max_size = "${var.redis_blue_max_size}"
    desired_capacity = "${var.redis_blue_desired_capacity}"
}

module "redis-green" {
    source = "../redis"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.name_prefix}-redis-green"
    dbsilo_name = "${var.dbsilo_name}"
    cluster_name = "${var.cluster_name}"

    ami_id = "${var.redis_green_ami_id}"
    instance_type = "${var.redis_green_instance_type}"
    min_size = "${var.redis_green_min_size}"
    max_size = "${var.redis_green_max_size}"
    desired_capacity = "${var.redis_green_desired_capacity}"
}
