provider "aws" {
    profile = "navopt_prod"
    region = "us-west-1"
}
resource "aws_launch_configuration" "redis_cluster_lc" {
    name_prefix = "tf-redis-lc-test-"
    image_id = "ami-b13377d1"
    instance_type = "r3.2xlarge"
    iam_instance_profile = "MongoDB_Server"
    ebs_optimized = true
    enable_monitoring = false
    key_name = "Baaz-Deployment"
    security_groups = ["sg-a8b7b5cd"]
    user_data = "{\"dbsilo\": \"dbsilo4\", \"service\": \"redis\", \"cluster\": \"alpha\", \"datadog_api_key\": \"42bbac658841fd4c44253c01423b3227\", \"backup_file\": \"s3://xplain-alpha/redis-backups/alpha-dump.rdb\"}"
    root_block_device {
        volume_size = 60
    }
    lifecycle {
        create_before_destroy = true
    }
}
resource "aws_autoscaling_group" "redis_cluster_asg" {
    name = "tf-redis-asg-test"
    max_size = 3
    min_size = 1
    launch_configuration = "${aws_launch_configuration.redis_cluster_lc.name}"
    desired_capacity = 1
    vpc_zone_identifier = ["subnet-6caca20e", "subnet-82145ec4"]
}
