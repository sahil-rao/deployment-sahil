output "admin_eip" {
    value = "${module.common.admin_eip}"
}

output "deployment_root_eip" {
    value = "${module.common.deployment_root_eip}"
}

output "frontend_fqdn" {
    value = "${aws_route53_record.frontend.fqdn}"
}
