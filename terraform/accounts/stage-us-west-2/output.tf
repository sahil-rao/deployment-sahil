output "admin_eip" {
    value = "${module.common.admin_eip}"
}

output "deployment_root_eip" {
    value = "${module.common.deployment_root_eip}"
}

output "nginx_public_eip" {
    value = "${module.common.nginx_public_eip}"
}