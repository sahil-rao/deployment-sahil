variable "vpc_id" {
    default = "vpc-81a5abe3"
}

variable "region" {
    default = "us-west-1"
}

variable "vpc_cidr" {
    default = "172.31.0.0/16"
}

variable "subnet_ids" {
    default = "subnet-6caca20e,subnet-82145ec4"
}

variable "cluster_name" {
    default = "alpha"
}

variable "datadog_api_key" {
    default = "450d437e4234a90b04a15396bd2a83b8"
}

variable "key_name" {
    default = "Baaz-Deployment"
}
