module "iam" {
    source = "../../services/iam"

    admin_name = "admin"
    elasticsearch_name = "elasticsearch"
    kibana_name = "kibana"
    logstash_name = "logstash"
    mongo_name = "mongo"
    nodejs_name = "nodejs"
    queue_server_name = "queue_server"
    redis_name = "redis"
}
