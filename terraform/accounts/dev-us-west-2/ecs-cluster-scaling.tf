resource "aws_autoscaling_policy" "ecs_cluster_loaded" {
  name                   = "more_powah"
  scaling_adjustment     = 2
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 10
  autoscaling_group_name = "ecs"
}

resource "aws_autoscaling_policy" "ecs_cluster_light" {
  name                   = "less_powah"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 10
  autoscaling_group_name = "ecs"
}
