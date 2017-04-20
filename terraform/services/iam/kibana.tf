resource "aws_iam_role" "kibana" {
    name = "${var.kibana_name}"
    assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    lifecycle {
        create_before_destroy = true
    }
}

resource "aws_iam_instance_profile" "kibana" {
    name = "${var.kibana_name}"
    role = "${aws_iam_role.kibana.name}"

    lifecycle {
        create_before_destroy = true
    }
}
