output "admin_security_groups" {
    value = ["${aws_security_group.admin.id}"]
}

output "backoffice_security_groups" {
    value = ["${aws_security_group.backoffice.id}"]
}

output "elasticsearch_security_groups" {
    value = ["${aws_security_group.elasticsearch.id}"]
}

output "logstash_security_groups" {
    value = ["${aws_security_group.logstash.id}"]
}

output "mongo_security_groups" {
    value = ["${aws_security_group.mongo.id}"]
}

output "nginx_security_groups" {
    value = ["${aws_security_group.nginx.id}"]
}

output "nodejs_security_groups" {
    value = ["${aws_security_group.nodejs.id}"]
}

output "queue_server_security_groups" {
    value = ["${aws_security_group.queue_server.id}"]
}

output "redis_security_groups" {
    value = ["${aws_security_group.redis.id}"]
}
