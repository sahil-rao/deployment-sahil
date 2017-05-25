
resource "aws_ecs_service" "navopt-compileservice-test" {
  name = "navopt-compileservice-test"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-compileservice-test.arn}"
  desired_count = 8
}

resource "aws_ecs_service" "navopt-applicationservice-test" {
  name = "navopt-applicationservice-test"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-applicationservice-test.arn}"
  desired_count = 4
}

resource "aws_ecs_service" "navopt-advanalytics-test" {
  name = "navopt-advanalytics-test"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-advanalytics-test.arn}"
  desired_count = 4
}

resource "aws_ecs_service" "navopt-mathservice-test" {
  name = "navopt-mathservice-test"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-mathservice-test.arn}"
  desired_count = 8
}

resource "aws_ecs_service" "navopt-apiservice-test" {
  name = "navopt-apiservice-test"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-apiservice-test.arn}"
  desired_count = 1
}

resource "aws_ecs_service" "navopt-dataaquisitionservice-test" {
  name = "navopt-dataaquisitionservice-test"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-dataaquisitionservice-test.arn}"
  desired_count = 2
}

resource "aws_ecs_service" "navopt-ruleengineservice-test" {
  name = "navopt-rulenengineservice-test"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-rulenengineservice-test.arn}"
  desired_count = 2
}
