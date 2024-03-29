resource "aws_security_group" "redis" {
    name = "${var.name}"
    vpc_id = "${var.vpc_id}"

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    ingress {
        from_port = 6379
        to_port = 6379
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    ingress {
        from_port = 26379
        to_port = 26379
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    ingress {
        from_port = 8
        to_port = 0
        protocol = "icmp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        ipv6_cidr_blocks = ["::/0"]
    }

    lifecycle {
        create_before_destroy = true
    }
}
