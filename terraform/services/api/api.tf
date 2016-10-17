variable "subnet_ids" { type = "list" }
variable "zone_id" {}

variable "api_elb_security_groups" { type = "list" }
variable "api_elb_internal" {}
variable "api_elb_dns_name" {}

variable "backoffice_instance_ids" { type = "list" }

resource "aws_elb" "api" {
    name = "api"
    subnets = ["${var.subnet_ids}"]
    security_groups = ["${var.api_elb_security_groups}"]

    listener {
      instance_port = 8982
      instance_protocol = "tcp"
      lb_port = 8982
      lb_protocol = "tcp"
    }

    connection_draining = true
    connection_draining_timeout = 60
    idle_timeout = 60

    instances = ["${var.backoffice_instance_ids}"]
    cross_zone_load_balancing = true
    // Public facing ELB
    internal = "${var.api_elb_internal}"
}

resource "aws_route53_record" "api" {
    zone_id = "${var.zone_id}"
    name = "${var.api_elb_dns_name}"
    type = "A"

    alias {
      name = "${aws_elb.api.dns_name}"
      zone_id = "${aws_elb.api.zone_id}"
      evaluate_target_health = true
    }
}

output "api_elb_fqdn" {
    value = "aws_route53_record.api.fqdn"
}
