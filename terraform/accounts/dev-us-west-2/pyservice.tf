resource "aws_ecr_repository" "navopt-pyservices" {
    name = "navopt-pyservices"
}

resource "aws_cloudwatch_log_group" "navopt-pyservices" {
  name = "navopt-pyservices"
  retention_in_days = "14"
}

resource "aws_ecs_task_definition" "navopt-pyservices" {
    family = "navopt-pyservices"
    
    volume {
        host_path = "/tmp/config.json"
        name = "config"
    }
    
    container_definitions = <<EOF
[
    {
        "name": "navopt-pyservices",
        "image": "${aws_ecr_repository.navopt-pyservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-pyservices.name}:latest",
        "cpu": 10,
        "memory": 100,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "mathservice" }
        ],
        "mountPoints": [
             {"containerPath":"/config.json", "sourceVolume":"config", "readOnly":null}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-pyservices.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_service" "navopt-pyservices" {
  name = "navopt-pyservices"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-pyservices.arn}"
  desired_count = 1
}