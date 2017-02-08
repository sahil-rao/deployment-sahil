resource "aws_security_group" "ecs" {
    name = "${var.name}"
    vpc_id = "${var.vpc_id}"

    ingress {
        from_port = 1
        to_port = 65535
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags {
        Name = "${var.name}"
    }
}
