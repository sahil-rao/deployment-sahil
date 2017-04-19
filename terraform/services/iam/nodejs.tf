resource "aws_iam_role" "nodejs" {
    name = "${var.nodejs_name}"
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

resource "aws_iam_role_policy" "nodejs" {
    name = "${var.nodejs_name}"
    role = "${aws_iam_role.nodejs.id}"
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

resource "aws_iam_instance_profile" "nodejs" {
    name = "${var.nodejs_name}"
    role = "${aws_iam_role.nodejs.name}"
}
