module "sg" {
    source = "../../services/sg"

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    vpc_cidr = "${data.terraform_remote_state.networking.vpc_cidr}"
    public_cidr = "${module.cloudera-exit-cidr.cidr}"

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
