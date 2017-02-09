variable "profile" {
    default = "navopt_stage"
}

variable "region" {
    default = "us-west-2"
}

variable "env" {
    default = "stage"
}

variable "terraform_remote_state_bucket" {
    default = "cloudera-terraform-infrastructure"
}

variable "terraform_remote_state_region" {
    default = "us-west-2"
}

variable "terraform_remote_state_key" {
    default = "stage/navopt-us-west-2-staging/terraform.tfstate"
}

variable "cluster_name" {
    default = "stage"
}

variable "datadog_api_key" {
    default = "450d437e4234a90b04a15396bd2a83b8"
}

variable "key_name" {
    default = "navopt-us-west-2-stage"
}

variable "s3_redis_backups_expiration_days" {
    default = 7
}

variable "cloudwatch_retention_in_days" {
    default = "14"
}
