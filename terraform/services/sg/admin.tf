resource "aws_security_group" "admin" {
    name = "${var.admin_name}"
    vpc_id = "${var.vpc_id}"

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidrs}"]
    }

    ingress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["${var.public_cidr}"]
    }

    ingress {
        from_port = 443
        to_port = 443
        protocol = "tcp"
        cidr_blocks = ["${var.public_cidr}"]
    }

    ingress {
        from_port = 3000
        to_port = 3000
        protocol = "tcp"
        cidr_blocks = ["${var.vpc_cidrs}"]
    }

    ingress {
        from_port = 8
        to_port = 0
        protocol = "icmp"
        cidr_blocks = ["${var.vpc_cidrs}"]
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
