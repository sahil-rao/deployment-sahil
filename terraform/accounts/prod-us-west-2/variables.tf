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
    default = "subnet-c0022ab4,subnet-9b8688f9,subnet-80074dc6"
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
