resource "aws_s3_bucket" "deployment_artifacts" {
    bucket = "navopt-dev-deployment-bucket"
    acl = "private"
}
