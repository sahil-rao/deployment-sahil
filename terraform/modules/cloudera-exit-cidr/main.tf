variable "cloudera_exit_cidr" {
    description = "Exit IP range of Cloudera corporate network"
    // Technically, our exit range is 101-120, but that can't be
    // described in one CIDR range. The smallest enclosing range
    // is the block from 96-127.
    default = "74.217.76.96/27"
}

output "cidr" {
    value = "${var.cloudera_exit_cidr}"
}
