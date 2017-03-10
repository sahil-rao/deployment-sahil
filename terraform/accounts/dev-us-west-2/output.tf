output "admin_eip" {
    value = "${module.common.admin_eip}"
}

output "frontend_fqdn" {
    value = "${aws_route53_record.frontend.fqdn}"
}
