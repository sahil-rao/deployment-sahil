variable "name" {}
variable "vpc_id" {}
variable "domain_name" {}

resource "aws_vpc_dhcp_options" "dns_resolver" {
    domain_name = "${var.domain_name}"
    domain_name_servers = ["AmazonProvidedDNS"]

    tags {
        Name = "${var.name}"
        Terraform = "managed"
    }
}

resource "aws_vpc_dhcp_options_association" "dns_resolver" {
    vpc_id = "${var.vpc_id}"
    dhcp_options_id = "${aws_vpc_dhcp_options.dns_resolver.id}"
}
