resource "aws_s3_bucket" "deployment_artifacts" {
    bucket = "navopt-${var.env}-deployment-bucket"
    acl = "private"
}
