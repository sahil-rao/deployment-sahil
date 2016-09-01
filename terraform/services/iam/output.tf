output "admin_role_name" {
    value = "${var.admin_name}"
}

output "admin_instance_profile" {
    value = "${aws_iam_instance_profile.admin.name}"
}

output "backoffice_role_name" {
    value = "${var.backoffice_name}"
}

output "backoffice_instance_profile" {
    value = "${aws_iam_instance_profile.backoffice.name}"
}

output "elasticsearch_role_name" {
    value = "${var.elasticsearch_name}"
}

output "elasticsearch_instance_profile" {
    value = "${aws_iam_instance_profile.elasticsearch.name}"
}

output "logstash_role_name" {
    value = "${var.logstash_name}"
}

output "logstash_instance_profile" {
    value = "${aws_iam_instance_profile.logstash.name}"
}

output "mongo_role_name" {
    value = "${var.mongo_name}"
}

output "mongo_instance_profile" {
    value = "${aws_iam_instance_profile.mongo.name}"
}

output "nginx_role_name" {
    value = "${var.nginx_name}"
}

output "nginx_instance_profile" {
    value = "${aws_iam_instance_profile.nginx.name}"
}

output "nodejs_role_name" {
    value = "${var.nodejs_name}"
}

output "nodejs_instance_profile" {
    value = "${aws_iam_instance_profile.nodejs.name}"
}

output "queue_server_role_name" {
    value = "${var.queue_server_name}"
}

output "queue_server_instance_profile" {
    value = "${aws_iam_instance_profile.queue_server.name}"
}

output "redis_role_name" {
    value = "${var.redis_name}"
}

output "redis_instance_profile" {
    value = "${aws_iam_instance_profile.redis.name}"
}
