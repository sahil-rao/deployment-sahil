resource "aws_iam_role" "queue_server" {
    name = "${var.iam_role_name}"
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

resource "aws_iam_instance_profile" "queue_server" {
    name = "${var.iam_role_name}"
    roles = ["${aws_iam_role.queue_server.name}"]
}
