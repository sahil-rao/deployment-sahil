variable "env" {}

# Networking
variable "region" {}
variable "vpc_id" {}
variable "private_cidrs" {
    type = "list"
}
variable "public_cidrs" {
    type = "list"
}
variable "private_subnet_ids" {
    type = "list"
}
variable "public_subnet_ids" {
    type = "list"
}

# DNS
variable "dns_zone_id" {}
variable "dns_zone_name" {}

# Instances
variable "key_name" {}
variable "instance_managed_policies" { type = "list" }
variable "num_instance_managed_policies" {}

# Admin
variable "admin_name" {
    default = "admin"
}
variable "admin_instance_type" {
    default = "t2.micro"
}

# Backoffice
variable "backoffice_instance_type" {}
variable "backoffice_instance_count" {}

# Logging
variable "cloudwatch_retention_in_days" {}

variable "logging_elasticsearch_version" {}
variable "logging_elasticsearch_ami" {}
variable "logging_elasticsearch_instance_type" {
    default = "t2.micro"
}
variable "logging_elasticsearch_min_size" {
    default = 0
}
variable "logging_elasticsearch_max_size" {
    default = 1
}
variable "logging_elasticsearch_desired_capacity" {
    default = 1
}
variable "logging_elasticsearch_heap_size" {
    default = "512m"
}

# Logging Redis
variable "logging_redis_version" {}
variable "logging_redis_ami" {}
variable "logging_redis_instance_type" {
    default = "t2.micro"
}
variable "logging_redis_min_size" {
    default = 0
}
variable "logging_redis_max_size" {
    default = 1
}
variable "logging_redis_desired_capacity" {
    default = 1
}
variable "logging_redis_quorum_size" {
    default = 1
}

# Redis Cache
variable "redis_cache_version" {}
variable "redis_cache_ami" {}
variable "redis_cache_instance_type" {
    default = "t2.micro"
}
variable "redis_cache_min_size" {
    default = 0
}
variable "redis_cache_max_size" {
    default = 1
}
variable "redis_cache_desired_capacity" {
    default = 1
}
variable "redis_cache_quorum_size" {
    default = 1
}

# Datadog
variable "datadog_api_key" {}

# S3
variable "s3_redis_backups_expiration_days" {}

# elb
variable "account_tls_cert_arn" {}
variable "nodejs_elb_internal" {}
