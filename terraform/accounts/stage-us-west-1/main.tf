provider "aws" {
    profile = "navopt_prod"
    region = "${var.region}"
}

module "dbsilo2" {
   source = "../../dbsilo"

   vpc_id = "${var.vpc_id}"
   vpc_cidr = "${var.vpc_cidr}"
   subnet_ids = "${var.subnet_ids}"

   key_name = "${var.key_name}"

   name_prefix = "${var.cluster_name}-dbsilo2"
   dbsilo_name = "dbsilo2"
   cluster_name = "${var.cluster_name}"
   datadog_api_key = "${var.datadog_api_key}"

   mongo_blue_ami_id = "ami-a699ddc6"
   mongo_blue_instance_type = "m4.xlarge"
   mongo_blue_min_size = 1
   mongo_blue_max_size = 3
   mongo_blue_desired_capacity = 3

   mongo_green_ami_id = "ami-a699ddc6"
   mongo_green_instance_type = "m4.xlarge"
   mongo_green_min_size = 0
   mongo_green_max_size = 0
   mongo_green_desired_capacity = 0

   redis_blue_ami_id = "ami-319bdf51"
   redis_blue_instance_type = "r3.2xlarge"
   redis_blue_min_size = 0
   redis_blue_max_size = 0
   redis_blue_desired_capacity = 0

   redis_green_ami_id = "ami-319bdf51"
   redis_green_instance_type = "r3.2xlarge"
   redis_green_min_size = 0
   redis_green_max_size = 0
   redis_green_desired_capacity = 0

   elasticsearch_blue_ami_id = "ami-bb9bdfdb"
   elasticsearch_blue_instance_type = "m3.xlarge"
   elasticsearch_blue_min_size = 0
   elasticsearch_blue_max_size = 0
   elasticsearch_blue_desired_capacity = 0

   elasticsearch_green_ami_id = "ami-bb9bdfdb"
   elasticsearch_green_instance_type = "m3.xlarge"
   elasticsearch_green_min_size = 0
   elasticsearch_green_max_size = 0
   elasticsearch_green_desired_capacity = 0
}

module "dbsilo4" {
    source = "../../dbsilo"

    vpc_id = "${var.vpc_id}"
    vpc_cidr = "${var.vpc_cidr}"
    subnet_ids = "${var.subnet_ids}"

    key_name = "${var.key_name}"

    name_prefix = "${var.cluster_name}-dbsilo4"
    dbsilo_name = "dbsilo4"
    cluster_name = "${var.cluster_name}"
    datadog_api_key = "${var.datadog_api_key}"

    mongo_blue_ami_id = "ami-a699ddc6"
    mongo_blue_instance_type = "m4.xlarge"
    mongo_blue_min_size = 1
    mongo_blue_max_size = 3
    mongo_blue_desired_capacity = 3

    mongo_green_ami_id = "ami-a699ddc6"
    mongo_green_instance_type = "m4.xlarge"
    mongo_green_min_size = 1
    mongo_green_max_size = 3
    mongo_green_desired_capacity = 3

    redis_blue_ami_id = "ami-179eda77"
    redis_blue_instance_type = "r3.2xlarge"
    redis_blue_min_size = 1
    redis_blue_max_size = 3
    redis_blue_desired_capacity = 3
    redis_blue_backup_file = "s3://xplain-alpha/redis-backups/${var.cluster_name}-dump.rdb"

    redis_green_ami_id = "ami-179eda77"
    redis_green_instance_type = "r3.2xlarge"
    redis_green_min_size = 0
    redis_green_max_size = 0
    redis_green_desired_capacity = 0
    redis_green_backup_file = "s3://xplain-alpha/redis-backups/${var.cluster_name}-dump.rdb"

    elasticsearch_blue_ami_id = "ami-bb9bdfdb"
    elasticsearch_blue_instance_type = "m3.xlarge"
    elasticsearch_blue_min_size = 0
    elasticsearch_blue_max_size = 0
    elasticsearch_blue_desired_capacity = 0

    elasticsearch_green_ami_id = "ami-bb9bdfdb"
    elasticsearch_green_instance_type = "m3.xlarge"
    elasticsearch_green_min_size = 3
    elasticsearch_green_max_size = 3
    elasticsearch_green_desired_capacity = 3
}
