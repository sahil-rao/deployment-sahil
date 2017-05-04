resource "aws_ecr_repository" "navopt-pyservices" {
    name = "navopt-pyservices"
}

resource "aws_cloudwatch_log_group" "navopt-pyservices" {
  name = "navopt-pyservices"
  retention_in_days = "14"
}

resource "aws_ecs_task_definition" "navopt-mathservice" {
    family = "navopt-mathservice"
    
    volume {
        host_path = "/tmp/config.json"
        name = "config"
    }
    
    container_definitions = <<EOF
[
    {
        "name": "mathservice",
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

resource "aws_ecs_task_definition" "navopt-ruleengineservice" {
    family = "navopt-ruleengineservice"
    
    volume {
        host_path = "/tmp/config.json"
        name = "config"
    }
    
    container_definitions = <<EOF
[
    {
        "name": "ruleengineservice",
        "image": "${aws_ecr_repository.navopt-pyservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-pyservices.name}:latest",
        "cpu": 10,
        "memory": 100,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "ruleengineservice" }
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

resource "aws_ecs_task_definition" "navopt-elasticpub" {
    family = "navopt-elasticpub"
    
    volume {
        host_path = "/tmp/config.json"
        name = "config"
    }
    
    container_definitions = <<EOF
[
    {
        "name": "elasticpub",
        "image": "${aws_ecr_repository.navopt-pyservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-pyservices.name}:latest",
        "cpu": 10,
        "memory": 100,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "elasticpub" }
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

resource "aws_ecs_task_definition" "navopt-dataacquisitionservice" {
    family = "navopt-dataacquisitionservice"
    
    volume {
        host_path = "/tmp/config.json"
        name = "config"
    }
    
    container_definitions = <<EOF
[
    {
        "name": "dataacquisitionservice",
        "image": "${aws_ecr_repository.navopt-pyservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-pyservices.name}:latest",
        "cpu": 10,
        "memory": 100,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "dataacquisitionservice" }
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

resource "aws_ecs_service" "navopt-mathservice" {
  name = "navopt-mathservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-mathservice.arn}"
  desired_count = 0
}

resource "aws_ecs_service" "navopt-ruleengineservice" {
  name = "navopt-ruleengineservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-ruleengineservice.arn}"
  desired_count = 0
}

resource "aws_ecs_service" "navopt-elasticpub" {
  name = "navopt-elasticpub"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-elasticpub.arn}"
  desired_count = 0
}

resource "aws_ecs_service" "navopt-dataacquisitionservice" {
  name = "navopt-dataacquisitionservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-dataacquisitionservice.arn}"
  desired_count = 0
}