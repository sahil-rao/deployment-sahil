variable "vpc_id" {
    default = "vpc-2f858b4d"
}

variable "region" {
    default = "us-west-2"
}

variable "vpc_cidr" {
    default = "172.31.0.0/16"
}

variable "subnet_ids" {
    default = "subnet-6caca20e,subnet-82145ec4"
}

variable "cluster_name" {
    default = "app"
}

variable "datadog_api_key" {
    default = "42bbac658841fd4c44253c01423b3227"
}

variable "key_name" {
    default = "XplainIO-Release-Deployment"
}
