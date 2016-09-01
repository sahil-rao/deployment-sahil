module "iam" {
    source = "../../services/iam"

    admin_name = "admin"
    backoffice_name = "backoffice"
    elasticsearch_name = "elasticsearch"
    logstash_name = "logstash"
    mongo_name = "mongo"
    nginx_name = "nginx"
    nodejs_name = "nodejs"
    queue_server_name = "queue_server"
    redis_name = "redis"
}
