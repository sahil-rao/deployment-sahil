resource "aws_security_group" "deployment-root" {
    name = "${var.deployment_root_name}"
    vpc_id = "${var.vpc_id}"

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["${var.public_cidr}"]
    }

    # FIXME: hack for harshil
    ingress {
        from_port = 8982
        to_port = 8982
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidrs}"]
    }

    ingress {
        from_port = 8
        to_port = 0
        protocol = "icmp"
        cidr_blocks = ["${var.public_cidr}"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    lifecycle {
        create_before_destroy = true
    }

    tags {
        Terraform = "managed"
    }
}
