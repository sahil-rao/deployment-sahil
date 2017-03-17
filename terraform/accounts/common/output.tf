output "admin_eip" {
    value = "${module.admin.eip}"
}

output "redis_instance_profile" {
    value = "${module.iam.redis_instance_profile}"
}

output "redis_security_groups" {
    value = "${module.sg.redis_security_groups}"
}

output "log_subscription_destination_arn" {
    value = "${module.log-service.destination_arn}"
}
