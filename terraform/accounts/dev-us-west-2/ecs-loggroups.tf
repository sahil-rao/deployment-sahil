
resource "aws_cloudwatch_log_group" "navopt-applicationservice-test" {
  name = "navopt-applicationservice-test"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-mathservice-test" {
  name = "navopt-mathservice-test"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-compileservice-test" {
  name = "navopt-compileservice-test"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-advanalytics-test" {
  name = "navopt-advanalytics-test"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-apiservice-test" {
  name = "navopt-apiservice-test"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-ruleengineservice-test" {
  name = "navopt-ruleengineservice-test"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-dataaquisitionservice-test" {
  name = "navopt-dataaquisitionservice-test"
  retention_in_days = "14"
}
