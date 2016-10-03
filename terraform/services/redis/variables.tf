variable "name" {}
variable "env" {}
variable "service" {}
variable "version" {}

###################################################################

variable "zone_name" {}
variable "security_groups" {
    type = "list"
}
variable "subnet_ids" {
    type = "list"
}

variable "key_name" {}
variable "iam_instance_profile" {}

###################################################################

variable "ami_id" {}
variable "instance_type" {}
variable "min_size" {
    default = 1
}
variable "max_size" {
    default = 1
}
variable "desired_capacity" {
    default = 1
}

variable "ebs_optimized" {
    default = true
}

###################################################################

variable "backup_file" {
    default = ""
}

variable "datadog_api_key" {}
variable "quorum_size" {
    default = 1
}
variable "backups_enabled" {
    default = "false"
}
