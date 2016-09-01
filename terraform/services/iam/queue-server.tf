resource "aws_iam_role" "queue_server" {
    name = "${var.queue_server_name}"
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
    name = "${var.queue_server_name}"
    roles = ["${aws_iam_role.queue_server.name}"]
}
