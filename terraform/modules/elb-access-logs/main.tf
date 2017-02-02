variable "region" {
    description = "region containing the the ELB instance"
}

variable "bucket" {
    type = "map"

    default = {
        "us-west-2" = "cloudera-sre-us-west-2-prod-elb-access-logs"
    }
}

output "bucket" {
    value = "${var.bucket[var.region]}"
}
