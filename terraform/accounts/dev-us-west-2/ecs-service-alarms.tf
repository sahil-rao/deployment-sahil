resource "aws_cloudwatch_metric_alarm" "compile-service-loaded" {
  alarm_name          = "compile-service-loaded"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "2000"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-compileservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.compile_service_loaded.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "compile-service-light" {
  alarm_name          = "compile-service-light"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "200"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-compileservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.compile_service_light.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "math-service-loaded" {
  alarm_name          = "math-service-loaded"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "1600"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-mathservice.name}"
    ClusterName = "ecs"

  }

  alarm_actions     = ["${aws_appautoscaling_policy.math_service_loaded.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "math-service-light" {
  alarm_name          = "math-service-light"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "200"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-mathservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.math_service_light.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "rule-service-loaded" {
  alarm_name          = "rule-service-loaded"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "2000"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-ruleengineservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.ruleengine_service_loaded.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "rule-service-light" {
  alarm_name          = "rule-service-light"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "200"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-ruleengineservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.ruleengine_service_light.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "application-service-loaded" {
  alarm_name          = "application-service-loaded"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "2000"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-applicationservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.application_service_loaded.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "application-service-light" {
  alarm_name          = "application-service-light"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "200"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-applicationservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.application_service_light.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "api-service-loaded" {
  alarm_name          = "api-service-loaded"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "2000"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-apiservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.api_service_loaded.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "api-service-light" {
  alarm_name          = "api-service-light"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "200"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-apiservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.api_service_light.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "advanalytics-loaded" {
  alarm_name          = "advanalytics-loaded"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "700"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-apiservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.advanalytics_loaded.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "advanalytics-light" {
  alarm_name          = "advanalytics-light"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "200"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-advanalytics.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.advanalytics_light.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "dataaquisition-service-loaded" {
  alarm_name          = "dataaquisition-service-loaded"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "2000"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-dataaquisitionservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.dataaquisition_service_loaded.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "dataaquisition-service-light" {
  alarm_name          = "dataaquisition-service-light"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Average"
  threshold           = "200"

  dimensions {
    ServiceName = "${aws_ecs_service.navopt-dataaquisitionservice.name}"
    ClusterName = "ecs"
  }

  alarm_actions     = ["${aws_appautoscaling_policy.dataaquisition_service_light.arn}"]
}
