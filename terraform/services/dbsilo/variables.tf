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
