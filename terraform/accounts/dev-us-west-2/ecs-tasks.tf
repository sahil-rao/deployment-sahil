resource "aws_ecs_task_definition" "navopt-applicationservice-test" {
    family = "navopt-applicationservice"
    container_definitions = <<EOF
[
    {
        "name": "applicationservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memory": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "applicationservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-applicationservice-test.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-compileservice-test" {
    family = "navopt-compileservice"
    container_definitions = <<EOF
[
    {
        "name": "compileservice",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 10,
        "memory": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "compileservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-compileservice-test.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-advanalytics-test" {
    family = "navopt-advanalytics"
    container_definitions = <<EOF
[
    {
        "name": "advanalytics",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 11,
        "memory": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "advanalytics" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-advanalytics-test.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-apiservice-test" {
    family = "navopt-advanalytics"
    container_definitions = <<EOF
[
    {
        "name": "advanalytics",
        "image": "${aws_ecr_repository.navopt-javaservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-javaservices.name}:latest",
        "cpu": 11,
        "memory": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "apiservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-apiservice-test.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-mathservice-test" {
    family = "navopt-mathservice"

   container_definitions = <<EOF
[
    {
        "name": "mathservice",
        "image": "${aws_ecr_repository.navopt-pyservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-pyservices.name}:latest",
        "cpu": 10,
        "memory": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "mathservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-mathservice-test.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}


resource "aws_ecs_task_definition" "navopt-ruleengineservice-test" {
    family = "navopt-ruleengineservice"

    container_definitions = <<EOF
[
    {
        "name": "ruleengineservice",
        "image": "${aws_ecr_repository.navopt-pyservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-pyservices.name}:latest",
        "cpu": 10,
        "memory": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "ruleengineservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-ruleengineservice-test.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-elasticpub-test" {
    family = "navopt-elasticpub"
    container_definitions = <<EOF
[
    {
        "name": "elasticpub",
        "image": "${aws_ecr_repository.navopt-pyservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-pyservices.name}:latest",
        "cpu": 10,
        "memory": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "elasticpub" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-elasticpub-test.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}

resource "aws_ecs_task_definition" "navopt-dataacquisitionservice-test" {
    family = "navopt-dataacquisitionservice"
    container_definitions = <<EOF
[
    {
        "name": "dataacquisitionservice",
        "image": "${aws_ecr_repository.navopt-pyservices.registry_id}.dkr.ecr.${var.region}.amazonaws.com/${aws_ecr_repository.navopt-pyservices.name}:latest",
        "cpu": 10,
        "memory": 1024,
        "essential": true,
        "command": [
        ],
        "environment": [
            { "name": "SERVICE_NAME", "value": "dataacquisitionservice" }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${aws_cloudwatch_log_group.navopt-dataaquisitionservice-test.name}",
                "awslogs-region": "${var.region}"
            }
        }
    }
]
EOF
}
