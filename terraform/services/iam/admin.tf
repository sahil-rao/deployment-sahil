resource "aws_iam_role" "admin" {
    name = "${var.admin_name}"
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

resource "aws_iam_role_policy" "admin" {
    name = "${var.admin_name}"
    role = "${aws_iam_role.admin.id}"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "admin" {
    name = "${var.admin_name}"
    roles = ["${aws_iam_role.admin.name}"]
}
