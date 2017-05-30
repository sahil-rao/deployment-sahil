resource "aws_ecs_task_definition" "navopt-applicationservice" {
    family = "navopt-applicationservice"
    container_definitions = <<EOF
[
    {
        "name": "applicationservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memoryReservation": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "applicationservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-applicationservice.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-compileservice" {
    family = "navopt-compileservice"
    container_definitions = <<EOF
[
    {
        "name": "compileservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memoryReservation": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "compileservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-compileservice.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-advanalytics" {
    family = "navopt-advanalytics"
    container_definitions = <<EOF
[
    {
        "name": "advanalytics",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 11,
        "memoryReservation": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "advanalytics" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-advanalytics.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-apiservice" {
    family = "navopt-apiservice"
    container_definitions = <<EOF
[
    {
        "name": "apiservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 11,
        "memoryReservation": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "apiservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-apiservice.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-mathservice" {
    family = "navopt-mathservice"

   container_definitions = <<EOF
[
    {
        "name": "mathservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memoryReservation": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "mathservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-mathservice.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}


resource "aws_ecs_task_definition" "navopt-ruleengineservice" {
    family = "navopt-ruleengineservice"

    container_definitions = <<EOF
[
    {
        "name": "ruleengineservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memoryReservation": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "ruleengineservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-ruleengineservice.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-elasticpub" {
    family = "navopt-elasticpub"
    container_definitions = <<EOF
[
    {
        "name": "elasticpub",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memoryReservation": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "elasticpub" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-elasticpub.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-dataacquisitionservice" {
    family = "navopt-dataacquisitionservice"
    container_definitions = <<EOF
[
    {
        "name": "dataacquisitionservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memoryReservation": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "dataacquisitionservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-dataaquisitionservice.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-datadog" {
    family = "dd-agent-task"

    volume {
        host_path = "/var/run/docker.sock"
        name = "docker_sock"
    }

    volume {
        host_path = "/proc/"
        name = "proc"
    }

    volume {
        host_path = "/cgroup/"
        name = "cgroup"
    }

    container_definitions = <<EOF
[
    {
        "name": "dd-agent",
        "image": "datadog/docker-dd-agent:latest",
        "cpu": 10,
        "memoryReservation": 128,
        "essential": true,
        "mountPoints": [ {
                "containerPath": "/var/run/docker.sock",
                "sourceVolume": "docker_sock"
            },
            {
                "containerPath": "/host/sys/fs/cgroup",
                "sourceVolume": "cgroup",
                "readOnly": true
            },
            {
                "containerPath": "/host/proc",
                "sourceVolume": "proc",
                "readOnly": true
            }
        ],
        "environment": [
            {
                "name": "API_KEY",
                "value": "${var.datadog_api_key}"
            }
        ]
    }
]
EOF
}
