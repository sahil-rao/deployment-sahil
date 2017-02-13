variable "profile" {
    default = "navopt_prod"
}

variable "region" {
    default = "us-west-2"
}

variable "env" {
    default = "prod"
}

variable "terraform_remote_state_bucket" {
    default = "cloudera-terraform-infrastructure"
}

variable "terraform_remote_state_region" {
    default = "us-west-2"
}

variable "terraform_remote_state_key" {
    default = "prod/navopt-us-west-2-prod/terraform.tfstate"
}

variable "cluster_name" {
    default = "prod"
}

variable "datadog_api_key" {
    default = "450d437e4234a90b04a15396bd2a83b8"
}

variable "key_name" {
    default = "navopt-us-west-2-prod"
}

variable "s3_redis_backups_expiration_days" {
    default = "30"
}

variable "cloudwatch_retention_in_days" {
    default = "365"
}

variable "old_vpc_cidr" {
    default = "172.31.0.0/16"
}
