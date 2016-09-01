resource "aws_s3_bucket" "backups" {
    bucket = "navopt-backups-${var.env}"
    acl = "private"

    lifecycle_rule {
        id = "redis-backups"
        prefix = "redis-backups/"
        enabled = true

        expiration {
            days = 5
        }
    }
}
