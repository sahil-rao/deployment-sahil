variable "vpc_id" {}
variable "private_cidrs" {
    type = "list"
}
variable "public_cidrs" {
    type = "list"
}

variable "admin_name" {}
variable "api_elb_name" {}
variable "deployment_root_name" {}
variable "kibana_name" {}
variable "logstash_name" {}
variable "mongo_name" {}
variable "nodejs_name" {}
variable "queue_server_name" {}
variable "navopt_elb_name" {}
