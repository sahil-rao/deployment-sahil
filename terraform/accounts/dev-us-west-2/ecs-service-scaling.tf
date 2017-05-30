resource "aws_appautoscaling_target" "compile_service" {
  max_capacity       = 30
  min_capacity       = 10
  resource_id        = "service/ecs/navopt-compileservice"
  role_arn           = "arn:aws:iam::128669107540:role/ecsAutoscaleRole"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "compile_service_loaded" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-up-compile"
  resource_id             = "service/ecs/navopt-compileservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = 1
  }

  depends_on = ["aws_appautoscaling_target.compile_service"]
}

resource "aws_appautoscaling_policy" "compile_service_light" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-down-compile"
  resource_id             = "service/ecs/navopt-compileservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = -1
  }

  depends_on = ["aws_appautoscaling_target.compile_service"]
}

resource "aws_appautoscaling_target" "math_service" {
  max_capacity       = 30
  min_capacity       = 10
  resource_id        = "service/ecs/navopt-mathservice"
  role_arn           = "arn:aws:iam::128669107540:role/ecsAutoscaleRole"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "math_service_loaded" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-up-math"
  resource_id             = "service/ecs/navopt-mathservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = 1
  }

  depends_on = ["aws_appautoscaling_target.math_service"]
}

resource "aws_appautoscaling_policy" "math_service_light" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-down-math"
  resource_id             = "service/ecs/navopt-mathservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = -1
  }

  depends_on = ["aws_appautoscaling_target.math_service"]
}

resource "aws_appautoscaling_target" "application_service" {
  max_capacity       = 30
  min_capacity       = 2
  resource_id        = "service/ecs/navopt-applicationservice"
  role_arn           = "arn:aws:iam::128669107540:role/ecsAutoscaleRole"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "application_service_loaded" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-up-application"
  resource_id             = "service/ecs/navopt-applicationservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = 1
  }

  depends_on = ["aws_appautoscaling_target.application_service"]
}

resource "aws_appautoscaling_policy" "application_service_light" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-down-application"
  resource_id             = "service/ecs/navopt-applicationservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = -1
  }

  depends_on = ["aws_appautoscaling_target.application_service"]
}

resource "aws_appautoscaling_target" "api_service" {
  max_capacity       = 30
  min_capacity       = 1
  resource_id        = "service/ecs/navopt-apiservice"
  role_arn           = "arn:aws:iam::128669107540:role/ecsAutoscaleRole"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_service_loaded" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-up-api"
  resource_id             = "service/ecs/navopt-apiservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = 1
  }

  depends_on = ["aws_appautoscaling_target.api_service"]
}

resource "aws_appautoscaling_policy" "api_service_light" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-down-api"
  resource_id             = "service/ecs/navopt-apiservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = -1
  }

  depends_on = ["aws_appautoscaling_target.api_service"]
}

resource "aws_appautoscaling_target" "ruleengine_service" {
  max_capacity       = 30
  min_capacity       = 2
  resource_id        = "service/ecs/navopt-ruleengineservice"
  role_arn           = "arn:aws:iam::128669107540:role/ecsAutoscaleRole"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ruleengine_service_loaded" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-up-rulengine"
  resource_id             = "service/ecs/navopt-ruleengineservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = 1
  }

  depends_on = ["aws_appautoscaling_target.ruleengine_service"]
}

resource "aws_appautoscaling_policy" "ruleengine_service_light" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-down-rulengine"
  resource_id             = "service/ecs/navopt-ruleengineservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = -1
  }

  depends_on = ["aws_appautoscaling_target.ruleengine_service"]
}

resource "aws_appautoscaling_target" "advanalytics" {
  max_capacity       = 30
  min_capacity       = 4
  resource_id        = "service/ecs/navopt-advanalytics"
  role_arn           = "arn:aws:iam::128669107540:role/ecsAutoscaleRole"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "advanalytics_loaded" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-up-advanalytics"
  resource_id             = "service/ecs/navopt-advanalytics"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = 1
  }

  depends_on = ["aws_appautoscaling_target.advanalytics"]
}

resource "aws_appautoscaling_policy" "advanalytics_light" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-down-advanalytics"
  resource_id             = "service/ecs/navopt-advanalytics"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = -1
  }

  depends_on = ["aws_appautoscaling_target.advanalytics"]
}


resource "aws_appautoscaling_target" "dataaquisition_service" {
  max_capacity       = 30
  min_capacity       = 2
  resource_id        = "service/ecs/navopt-dataaquisitionservice"
  role_arn           = "arn:aws:iam::128669107540:role/ecsAutoscaleRole"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "dataaquisition_service_loaded" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-up-dataaquisition"
  resource_id             = "service/ecs/navopt-dataaquisitionservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = 1
  }

  depends_on = ["aws_appautoscaling_target.dataaquisition_service"]
}

resource "aws_appautoscaling_policy" "dataaquisition_service_light" {
  adjustment_type         = "ChangeInCapacity"
  cooldown                = 30
  metric_aggregation_type = "Average"
  name                    = "scale-down-dataaquisition"
  resource_id             = "service/ecs/navopt-dataaquisitionservice"
  scalable_dimension      = "ecs:service:DesiredCount"
  service_namespace       = "ecs"

  step_adjustment {
    metric_interval_lower_bound = 0
    scaling_adjustment          = -1
  }

  depends_on = ["aws_appautoscaling_target.dataaquisition_service"]
}
