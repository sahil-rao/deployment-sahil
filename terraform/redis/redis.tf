provider "aws" {
    access_key = ""
    secret_key = ""
    region = "us-west-1"
}
resource "aws_launch_configuration" "redis_cluster_lc" {
    image_id = "ami-5e195d3e"
    instance_type = "r3.2xlarge"
    iam_instance_profile = "MongoDB_Server"
    ebs_optimized = true
    enable_monitoring = false
    key_name = "Baaz-Deployment"
    security_groups = ["sg-a8b7b5cd"]
    user_data = "{\"dbsilo\": \"dbsilo4\", \"service\": \"redis\", \"cluster\": \"alpha\", \"datadog_api_key\": \"42bbac658841fd4c44253c01423b3227\"}"
}
resource "aws_autoscaling_group" "redis_cluster_asg" {
    max_size = 3
    min_size = 1
    launch_configuration = "${aws_launch_configuration.redis_cluster_lc.name}"
    desired_capacity = 1
    vpc_zone_identifier = ["subnet-6caca20e", "subnet-82145ec4"]
}
