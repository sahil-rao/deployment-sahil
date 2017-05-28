
###################################################################

module "ubuntu" {
    source = "../../modules/tf_aws_ubuntu_ami"
    region = "${var.region}"
    distribution = "trusty"
    virttype = "hvm"
    storagetype = "ebs-ssd"
}

resource "aws_instance" "default" {
    # FIXME: Production uses this AMI, which needs to be copied over to this image.
    # Backoffice-Foundation-07-16-2014 (ami-79b6cf49)
    ami = "${coalesce(var.ami, module.ubuntu.ami_id)}"
    vpc_security_group_ids = ["${aws_security_group.backoffice.id}"]
    subnet_id = "${element(var.subnet_ids, count.index)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${aws_iam_instance_profile.backoffice.name}"

    # FIXME: This is what's used in production.
    # instance_type = "c3.xlarge"
    # count = 2
    instance_type = "${var.instance_type}"
    count = "${var.instance_count}"

    tags {
        Terraform = "managed"
        Cluster = "${var.env}"
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}

###################################################################

resource "aws_elb" "api_backend" {
    name = "${var.api_backend_elb_name}"
    subnets = ["${var.subnet_ids}"]
    security_groups = ["${aws_security_group.api_backend_elb.id}"]

    instances = ["${aws_instance.default.*.id}"]

    listener {
      instance_port = 8982
      instance_protocol = "tcp"
      lb_port = 8982
      lb_protocol = "tcp"
    }

    // FIXME: Disable the health check for now.
    /*
    health_check {
      healthy_threshold = 10
      unhealthy_threshold = 2
      timeout = 5
      target = "HTTP:8983/healthz"
      interval = 10
    }
    */

    connection_draining = true
    connection_draining_timeout = 60
    idle_timeout = 60

    cross_zone_load_balancing = true
    internal = true
}

resource "aws_route53_record" "api_backend" {
    zone_id = "${var.dns_zone_id}"
    name = "${var.api_backend_dns_name}"
    type = "A"

    alias {
        name = "${aws_elb.api_backend.dns_name}"
        zone_id = "${aws_elb.api_backend.zone_id}"
        evaluate_target_health = true
    }
}

###################################################################

module "advanced-analytics-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "advanalytics"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "application-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "applicationservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "compile-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "compileservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "data-acquisition-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "dataacquisitionservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "elastic-pub-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "elasticpub"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "math-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "mathservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "rule-engine-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "ruleengineservice"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

module "navopt-api-service" {
    source = "../../modules/cloudwatch-log-group"

    name = "navoptapiserver"
    retention_in_days = "${var.cloudwatch_retention_in_days}"
    subscription_destination_arn = "${var.log_subscription_destination_arn}"
}

###################################################################

resource "aws_route53_record" "default" {
    zone_id = "${var.dns_zone_id}"
    count = "${var.instance_count}"
    name = "backoffice-${count.index}"
    type = "A"
    ttl = "5"
    records = ["${element(aws_instance.default.*.private_ip, count.index)}"]
}

###################################################################

output "instance_ids" {
    value = ["${aws_instance.default.*.id}"]
}
