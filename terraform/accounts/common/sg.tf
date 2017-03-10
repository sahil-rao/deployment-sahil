module "sg" {
    source = "../../services/sg"

    vpc_id = "${var.vpc_id}"
    private_cidrs = ["${var.private_cidrs}"]
    public_cidrs = ["${var.public_cidrs}"]

    admin_name = "admin"
    api_elb_name = "api-elb"
    deployment_root_name = "deployment-root"
    elasticsearch_name = "elasticsearch"
    kibana_name = "kibana"
    logstash_name = "logstash"
    mongo_name = "mongo"
    nodejs_name = "nodejs"
    queue_server_name = "queue_server"
    redis_name = "redis"
    navopt_elb_name = "navopt-elb"
}
