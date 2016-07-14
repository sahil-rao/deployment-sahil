output "vpc_id" {
    value = "${module.networking.vpc_id}"
}

output "vpc_cidr" {
    value = "${var.vpc_cidr}"
}

output "public_subnet_ids" {
    value = "${module.networking.public_subnet_ids}"
}

output "private_subnet_ids" {
    value = "${module.networking.private_subnet_ids}"
}

output "availability_zones" {
    value = "${var.availability_zones}"
}
