output "admin_eip" {
    value = "${module.admin.eip}"
}

output "log_subscription_destination_arn" {
    value = "${module.log-service.destination_arn}"
}
