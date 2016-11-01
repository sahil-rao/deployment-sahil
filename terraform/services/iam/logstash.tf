resource "aws_iam_role" "logstash" {
    name = "${var.logstash_name}"
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

resource "aws_iam_instance_profile" "logstash" {
    name = "${var.logstash_name}"
    roles = ["${aws_iam_role.logstash.name}"]

    lifecycle {
        create_before_destroy = true
    }
}
