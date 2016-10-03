module "s3" {
    source = "../../services/s3"

    env = "${var.env}"
    navopt_name = "navopt-${var.env}"
    backups_name = "navopt-backups-${var.env}"

    redis_expiration_days = 5
}