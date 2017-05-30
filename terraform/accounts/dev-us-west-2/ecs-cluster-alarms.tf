
resource "aws_cloudwatch_metric_alarm" "cluster-loaded" {
  alarm_name          = "cluster-loaded"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "30"

  dimensions {
    AutoScalingGroupName = "ecs"
  }

  alarm_actions     = ["${aws_autoscaling_policy.ecs_cluster_loaded.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "cluster-light" {
  alarm_name          = "cluster-light"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "10"

  dimensions {
    AutoScalingGroupName = "ecs"
  }

  alarm_actions     = ["${aws_autoscaling_policy.ecs_cluster_light.arn}"]
}
