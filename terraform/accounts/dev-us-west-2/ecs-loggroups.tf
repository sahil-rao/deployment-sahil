
resource "aws_cloudwatch_log_group" "navopt-applicationservice" {
  name = "navopt-applicationservice"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-mathservice" {
  name = "navopt-mathservice"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-compileservice" {
  name = "navopt-compileservice"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-advanalytics" {
  name = "navopt-advanalytics"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-apiservice" {
  name = "navopt-apiservice"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-ruleengineservice" {
  name = "navopt-ruleengineservice"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-dataaquisitionservice" {
  name = "navopt-dataaquisitionservice"
  retention_in_days = "14"
}

resource "aws_cloudwatch_log_group" "navopt-elasticpub" {
  name = "navopt-elasticpub"
  retention_in_days = "14"
}
