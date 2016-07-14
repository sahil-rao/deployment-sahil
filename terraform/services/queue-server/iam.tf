resource "aws_iam_role" "default" {
    name = "${var.name}"
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
}

resource "aws_iam_instance_profile" "default" {
    name = "${var.name}"
    roles = ["${aws_iam_role.default.name}"]
}
