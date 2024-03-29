output "admin_security_groups" {
    value = ["${aws_security_group.admin.id}"]
}

output "api_elb_security_groups" {
    value = ["${aws_security_group.api_elb.id}"]
}

output "deployment_root_security_groups" {
    value = ["${aws_security_group.deployment-root.id}"]
}

output "kibana_security_groups" {
    value = ["${aws_security_group.kibana.id}"]
}

output "logstash_security_groups" {
    value = ["${aws_security_group.logstash.id}"]
}

output "mongo_security_groups" {
    value = ["${aws_security_group.mongo.id}"]
}

output "nodejs_security_groups" {
    value = ["${aws_security_group.nodejs.id}"]
}

output "queue_server_security_groups" {
    value = ["${aws_security_group.queue_server.id}"]
}

output "nodejs_elb_security_groups" {
    value = ["${aws_security_group.elb.id}"]
}
