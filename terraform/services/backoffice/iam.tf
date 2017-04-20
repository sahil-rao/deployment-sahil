resource "aws_iam_role" "backoffice" {
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

resource "aws_iam_role_policy" "backoffice" {
    name = "${var.iam_role_name}"
    role = "${aws_iam_role.backoffice.id}"
    policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
      {
          "Effect": "Allow",
          "Action": [
              "ec2:DescribeInstances",
              "ec2:DescribeTags"
          ],
          "Resource": "*"
      },
      {
          "Effect": "Allow",
          "Action": "s3:*",
          "Resource": "${var.s3_navopt_bucket_arn}/xplain-servicelogs"
      },
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
      },
      {
          "Effect":"Allow",
          "Action":[
              "logs:CreateLogGroup",
              "logs:CreateLogStream",
              "logs:PutLogEvents"
          ],
          "Resource":[
              "*"
          ]
      }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "backoffice" {
    name = "${var.iam_role_name}"
    role = "${aws_iam_role.backoffice.name}"
}
