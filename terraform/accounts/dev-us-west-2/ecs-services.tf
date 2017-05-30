resource "aws_ecs_service" "navopt-compileservice" {
  name = "navopt-compileservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-compileservice.arn}"
  desired_count = 10
  deployment_minimum_healthy_percent = 75

  placement_strategy {
    type  = "spread"
    field = "instanceId"
  }
}

resource "aws_ecs_service" "navopt-applicationservice" {
  name = "navopt-applicationservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-applicationservice.arn}"
  desired_count = 2
  deployment_minimum_healthy_percent = 75

  placement_strategy {
    type  = "spread"
    field = "instanceId"
  }
}

resource "aws_ecs_service" "navopt-advanalytics" {
  name = "navopt-advanalytics"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-advanalytics.arn}"
  desired_count = 4
  deployment_minimum_healthy_percent = 75

  placement_strategy {
    type  = "spread"
    field = "instanceId"
  }
}

resource "aws_ecs_service" "navopt-mathservice" {
  name = "navopt-mathservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-mathservice.arn}"
  desired_count = 10
  deployment_minimum_healthy_percent = 75

  placement_strategy {
    type  = "spread"
    field = "instanceId"
  }
}

resource "aws_ecs_service" "navopt-apiservice" {
  name = "navopt-apiservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-apiservice.arn}"
  desired_count = 1
  deployment_minimum_healthy_percent = 75

  placement_strategy {
    type  = "spread"
    field = "instanceId"
  }
}

resource "aws_ecs_service" "navopt-dataaquisitionservice" {

  name = "navopt-dataaquisitionservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-dataacquisitionservice.arn}"
  desired_count = 2
  deployment_minimum_healthy_percent = 50

  placement_strategy {
    type  = "spread"
    field = "instanceId"
  }
}

resource "aws_ecs_service" "navopt-ruleengineservice" {
  name = "navopt-ruleengineservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-ruleengineservice.arn}"
  desired_count = 2
  deployment_minimum_healthy_percent = 50

  placement_strategy {
    type  = "spread"
    field = "instanceId"
  }
}
