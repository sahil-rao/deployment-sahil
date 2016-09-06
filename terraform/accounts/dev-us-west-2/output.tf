output "admin-eip" {
    value = "${module.admin.eip}"
}

output "deployment-root-eip" {
    value = "${module.deployment-root.eip}"
}

output "nginx-eip" {
    value = "${module.nginx.eip}"
}
