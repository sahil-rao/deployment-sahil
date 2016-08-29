variable "env" {}
variable "datadog_api_key" {}

##############################################################################

variable "region" {}
variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {
    type = "list"
}
variable "dns_zone_id" {}
variable "zone_name" {}

variable "key_name" {}

##############################################################################

variable "elasticsearch_name" {}
variable "elasticsearch_security_groups" {
    type = "list"
}
variable "elasticsearch_iam_instance_profile" {}

variable "elasticsearch_version" {}
variable "elasticsearch_ami_id" {}
variable "elasticsearch_instance_type" {}
variable "elasticsearch_min_size" {}
variable "elasticsearch_max_size" {}
variable "elasticsearch_desired_capacity" {}
variable "elasticsearch_ebs_optimized" {
    default = true
}

##############################################################################

variable "kibana_name" {}

variable "kibana_security_groups" {
    type = "list"
    default = []
}

variable "kibana_ami" {
    default = ""
}
variable "kibana_instance_type" {
    default = "t2.micro"
}
variable "kibana_instance_count" {
    default = 1
}
variable "kibana_iam_instance_profile" {
    default = ""
}
variable "kibana_ebs_optimized" {
    default = ""
}

##############################################################################

variable "logstash_name" {}

variable "logstash_security_groups" {
    type = "list"
    default = []
}

variable "logstash_ami" {
    default = ""
}
variable "logstash_instance_type" {
    default = "t2.micro"
}
variable "logstash_instance_count" {
    default = 1
}
variable "logstash_iam_instance_profile" {
    default = ""
}
variable "logstash_ebs_optimized" {
    default = ""
}

##############################################################################

variable "redis_name" {}
variable "redis_version" {}
variable "redis_service" {}

variable "redis_security_groups" {
    type = "list"
    default = []
}

variable "redis_ami_id" {
    default = ""
}
variable "redis_instance_type" {
    default = "t2.micro"
}
variable "redis_min_size" {}
variable "redis_max_size" {}
variable "redis_desired_capacity" {}
variable "redis_quorum_size" {}
variable "redis_iam_instance_profile" {
    default = ""
}
variable "redis_ebs_optimized" {
    default = ""
}
