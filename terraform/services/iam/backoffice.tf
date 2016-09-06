resource "aws_iam_role" "backoffice" {
    name = "${var.backoffice_name}"
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

resource "aws_iam_role_policy" "backoffice" {
    name = "${var.backoffice_name}"
    role = "${aws_iam_role.backoffice.id}"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
          "route53:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "backoffice" {
    name = "${var.backoffice_name}"
    roles = ["${aws_iam_role.backoffice.name}"]
}
