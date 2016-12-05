variable "environment" {
    description = "The type of environment: prod/staging/dev/etc"
}

variable "destination_arn" {
    description = "The destination stream that receives the logs"
    type = "map"

    default = {
        "dev" = "arn:aws:logs:us-west-2:966730426455:destination:log-service-dev"
        "stage" = "arn:aws:logs:us-west-2:966730426455:destination:log-service-dev"
        "test" = "arn:aws:logs:us-west-2:966730426455:destination:log-service-dev"
        "prod" = "arn:aws:logs:us-west-2:966730426455:destination:log-service-prod"
    }
}

##############################################################################

output "destination_arn" {
    value = "${var.destination_arn[var.environment]}"
}
