resource "aws_security_group" "backoffice" {
    name = "${var.sg_name}"
    vpc_id = "${var.vpc_id}"

    ingress {
        from_port = 26379
        to_port = 26379
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

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

    # FIXME: why?
    ingress {
        from_port = 7432
        to_port = 7432
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    # FIXME: why?
    ingress {
        from_port = 7180
        to_port = 7183
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    # FIXME: why?
    ingress {
        from_port = 5601
        to_port = 5601
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    # FIXME: hack for harshil
    ingress {
        from_port = 8982
        to_port = 8982
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    # FIXME: why?
    ingress {
        from_port = 9300
        to_port = 9300
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    # FIXME: why?
    ingress {
        from_port = 9200
        to_port = 9200
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

    lifecycle {
        create_before_destroy = true
    }

    tags {
        Terraform = "managed"
    }
}

resource "aws_security_group" "api_backend_elb" {
    name = "${var.api_backend_elb_sg_name}"
    vpc_id = "${var.vpc_id}"

    // Allow inbound internally originated traffic
    ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    // Service port
    egress {
        from_port = 8982
        to_port = 8982
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }

    // Health port
    egress {
        from_port = 8983
        to_port = 8983
        protocol = "tcp"
        cidr_blocks = ["${var.private_cidrs}"]
    }
}
