
resource "aws_ecr_repository" "navopt-javaservices" {
    name = "navopt-javaservices"
    retention_in_days = "31"
}

resource "aws_ecr_repository" "navopt-pyservices" {
    name = "navopt-pyservices"
    retention_in_days = "31"
}
