module "iam" {
    source = "../../services/iam"

    s3_navopt_bucket_arn = "${module.s3.navopt_arn}"

    admin_name = "admin"
    backoffice_name = "backoffice"
    elasticsearch_name = "elasticsearch"
    kibana_name = "kibana"
    logstash_name = "logstash"
    mongo_name = "mongo"
    nodejs_name = "nodejs"
    queue_server_name = "queue_server"
    redis_name = "redis"
}
