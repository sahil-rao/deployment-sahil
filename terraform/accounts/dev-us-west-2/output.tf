output "admin_eip" {
    value = "${module.common.admin_eip}"
}

output "api_fqdn" {
    value = "${module.common.api_elb_fqdn}"
}

output "deployment_root_eip" {
    value = "${module.common.deployment_root_eip}"
}

output "nginx_public_eip" {
    value = "${module.common.nginx_public_eip}"
}

output "nginx_private_eip" {
    value = "${module.common.nginx_private_eip}"
}

output "website_fqdn" {
    value = "${aws_route53_record.website.fqdn}"
}
