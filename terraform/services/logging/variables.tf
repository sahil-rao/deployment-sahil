variable "env" {}

##############################################################################

variable "region" {}
variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnet_ids" {}
variable "dns_zone_id" {}

variable "key_name" {}

##############################################################################

variable "elasticsearch_name" {}

variable "elasticsearch_security_groups" {
    default = ""
}

variable "elasticsearch_ami" {
    default = ""
}
variable "elasticsearch_instance_type" {
    default = "t2.micro"
}
variable "elasticsearch_instance_count" {
    default = 1
}
variable "elasticsearch_iam_instance_profile" {
    default = ""
}
variable "elasticsearch_ebs_optimized" {
    default = ""
}

##############################################################################

variable "logstash_name" {}

variable "logstash_security_groups" {
    default = ""
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

variable "redis_security_groups" {
    default = ""
}

variable "redis_ami" {
    default = ""
}
variable "redis_instance_type" {
    default = "t2.micro"
}
variable "redis_instance_count" {
    default = 1
}
variable "redis_iam_instance_profile" {
    default = ""
}
variable "redis_ebs_optimized" {
    default = ""
}
