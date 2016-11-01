variable "env" {}
variable "navopt_name" {}
variable "backups_name" {}
variable "redis_expiration_days" {}

resource "aws_s3_bucket" "navopt" {
    bucket = "${var.navopt_name}"
    acl = "private"

    tags {
        Name = "${var.navopt_name}"
        Environment = "${var.env}"
    }
}

resource "aws_s3_bucket" "backups" {
    bucket = "${var.backups_name}"
    acl = "private"

    lifecycle_rule {
        id = "redis-backups"
        prefix = "redis-backups/"
        enabled = true

        expiration {
            days = "${var.redis_expiration_days}"
        }
    }
}

output "navopt_arn" {
    value = "${aws_s3_bucket.navopt.arn}"
}

output "backup_arn" {
    value = "${aws_s3_bucket.backups.arn}"
}
