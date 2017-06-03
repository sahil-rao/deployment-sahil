module "navopt-applicationservice-log-group" {
    source = "../../modules/cloudwatch-log-group"
    name = "navopt-applicationservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}

module "navopt-mathservice-log-group" {
    source = "../../modules/cloudwatch-log-group"
    name = "navopt-mathservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}

module "navopt-compileservice-log-group" {
    source = "../../modules/cloudwatch-log-group"
    name = "navopt-compileservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}

module "navopt-advanalytics-log-group" {
    source = "../../modules/cloudwatch-log-group"
    name = "navopt-advanalytics"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}

module "navopt-apiservice-log-group" {
    source = "../../modules/cloudwatch-log-group"
    name = "navopt-apiservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}

module "navopt-ruleengineservice-log-group" {
    source = "../../modules/cloudwatch-log-group"
    name = "navopt-ruleengineservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}

module "navopt-dataaquisitionservice-log-group" {
    source = "../../modules/cloudwatch-log-group"
    name = "navopt-dataaquisitionservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}

module "navopt-elasticpub-log-group" {
    source = "../../modules/cloudwatch-log-group"
    name = "navopt-elasticpub"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${module.common.log_subscription_destination_arn}"
}
