variable "profile" {
    default = "navopt_dev"
}

variable "region" {
    default = "us-west-2"
}

variable "env" {
    default = "dev"
}

variable "terraform_remote_state_bucket" {
    default = "cloudera-terraform-infrastructure"
}

variable "terraform_remote_state_region" {
    default = "us-west-2"
}

variable "terraform_remote_state_key" {
    default = "dev/navopt-us-west-2-dev/terraform.tfstate"
}

variable "cluster_name" {
    default = "dev"
}

variable "datadog_api_key" {
    default = "450d437e4234a90b04a15396bd2a83b8"
}

variable "key_name" {
    default = "navopt-us-west-2-dev"
}
