output "admin_eip" {
    value = "${module.admin.eip}"
}

output "deployment_root_eip" {
    value = "${module.deployment-root.eip}"
}

output "nginx_public_eip" {
    value = "${module.nginx.public_eip}"
}

output "nginx_private_eip" {
    value = "${module.nginx.private_eip}"
}

output "elasticsearch_instance_profile" {
    value = "${module.iam.elasticsearch_instance_profile}"
}

output "mongo_instance_profile" {
    value = "${module.iam.mongo_instance_profile}"
}

output "redis_instance_profile" {
    value = "${module.iam.redis_instance_profile}"
}

output "elasticsearch_security_groups" {
    value = "${module.sg.elasticsearch_security_groups}"
}

output "mongo_security_groups" {
    value = "${module.sg.mongo_security_groups}"
}

output "redis_security_groups" {
    value = "${module.sg.redis_security_groups}"
}

output "log_subscription_destination_arn" {
    value = "${module.log-service.destination_arn}"
}
