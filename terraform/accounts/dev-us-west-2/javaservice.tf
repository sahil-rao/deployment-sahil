resource "aws_ecr_repository" "navopt-javaservices" {
    name = "navopt-javaservices"
}

resource "aws_cloudwatch_log_group" "navopt-javaservices" {
  name = "navopt-javaservices"
  retention_in_days = "14"
}

resource "aws_ecs_task_definition" "navopt-applicationservice" {
    family = "navopt-applicationservice"
    
    volume {
        host_path = "/tmp/config.json"
        name = "config"
    }
    
    container_definitions = <<EOF
[
    {
        "name": "applicationservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memory": 100,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "applicationservice" }
        ],
        "mountPoints": [
             {"containerPath":"/config.json", "sourceVolume":"config", "readOnly":null}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-javaservices.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-compileservice" {
    family = "navopt-compileservice"
    
    volume {
        host_path = "/tmp/config.json"
        name = "config"
    }
    
    container_definitions = <<EOF
[
    {
        "name": "compileservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memory": 100,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "compileservice" }
        ],
        "mountPoints": [
             {"containerPath":"/config.json", "sourceVolume":"config", "readOnly":null}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-javaservices.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-advanalytics" {
    family = "navopt-advanalytics"
    
    volume {
        host_path = "/tmp/config.json"
        name = "config"
    }
    
    container_definitions = <<EOF
[
    {
        "name": "advanalytics",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 11,
        "memory": 100,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "advanalytics" }
        ],
        "mountPoints": [
             {"containerPath":"/config.json", "sourceVolume":"config", "readOnly":null}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-javaservices.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_service" "navopt-compileservice" {
  name = "navopt-compileservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-compileservice.arn}"
  desired_count = 0
}

resource "aws_ecs_service" "navopt-applicationservice" {
  name = "navopt-applicationservice"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-applicationservice.arn}"
  desired_count = 0
}

resource "aws_ecs_service" "navopt-advanalytics" {
  name = "navopt-advanalytics"
  cluster = "${module.ecs.ecs_cluster_id}"
  task_definition = "${aws_ecs_task_definition.navopt-advanalytics.arn}"
  desired_count = 0
}