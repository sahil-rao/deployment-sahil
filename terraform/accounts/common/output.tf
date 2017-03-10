output "admin_eip" {
    value = "${module.admin.eip}"
}

output "deployment_root_eip" {
    value = "${module.deployment-root.eip}"
}

output "elasticsearch_instance_profile" {
    value = "${module.iam.elasticsearch_instance_profile}"
}

output "redis_instance_profile" {
    value = "${module.iam.redis_instance_profile}"
}

output "elasticsearch_security_groups" {
    value = "${module.sg.elasticsearch_security_groups}"
}

output "redis_security_groups" {
    value = "${module.sg.redis_security_groups}"
}

output "log_subscription_destination_arn" {
    value = "${module.log-service.destination_arn}"
}
