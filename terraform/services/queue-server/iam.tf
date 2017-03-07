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

resource "aws_iam_role_policy_attachment" "managed_policy_attachment" {
    count = "${var.num_instance_managed_policies}"
    role = "${aws_iam_role.queue_server.id}"
    policy_arn = "${element(var.instance_managed_policies, count.index)}"
}
