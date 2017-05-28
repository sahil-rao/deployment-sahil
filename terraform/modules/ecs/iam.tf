resource "aws_iam_role" "ecs" {
    name = "${var.name}"
    assume_role_policy = <<EOF
{
    "Version": "2008-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": [
                    "ecs.amazonaws.com",
                    "ec2.amazonaws.com"
                ]
            },
            "Effect": "Allow"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy" "ecs" {
    name = "${var.name}"
    role = "${aws_iam_role.ecs.id}"
    policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:BatchCheckLayerAvailability",
                "ecr:BatchGetImage",
                "ecr:GetAuthorizationToken",
                "ecr:GetDownloadUrlForLayer",
                "ecs:CreateCluster",
                "ecs:DeregisterContainerInstance",
                "ecs:DiscoverPollEndpoint",
                "ecs:Poll",
                "ecs:RegisterContainerInstance",
                "ecs:StartTask",
                "ecs:StartTelemetrySession",
                "ecs:Submit*",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
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
          "Resource": "arn:aws:s3:::navopt-dev/xplain-servicelogs"
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
        }
    ]
}
EOF
}

resource "aws_iam_instance_profile" "ecs" {
    name = "${var.name}"
    role = "${aws_iam_role.ecs.name}"
}
