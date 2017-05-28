variable "vpc_id" {}
variable "subnet_ids" {
    type = "list"
}
variable "private_cidrs" {
    type = "list"
}
variable "zone_id" {}
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

variable "elasticsearch_name" {}

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

variable "elasticsearch_heap_size" {}
