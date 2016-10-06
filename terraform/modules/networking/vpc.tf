# Provides common functionality and enforces all standards related
# to provisioning of VPC resources.

####################
# Required variables
####################

# What region should we provision resources?
variable "region" {}

# What is our VPC CIDR block
variable "vpc_cidr" {}

# VPC Name, with no spaces.
variable "vpc_name" {}

# A comma delimited string with private subnets CIDR
variable "private_subnets" {
    type = "list"
}

# A comma delimited string of public subnets CIDR
variable "public_subnets" {
    type = "list"
}

# What is your virtual gateway
variable "virtual_gateway_id" {}

# A comma delimited string of availability zones. Warning, the length of
# azs specified should be equal to the length max(private_subnets, public_subnets).
# reason is for each subnet, we lookup the same index in availability_zones list.
# example: availability_zones = "us-west-1a,us-west-1b,us-west-1c,us-west-1a"
# Note the repeated us-west-1a, since us-west-1 has only 3 AZs but we have 4 subnets
variable "availability_zones" {
    type = "list"
}

########################################
#Create resources specified in variables
########################################

# Our VPC
resource "aws_vpc" "vpc" {
    cidr_block = "${var.vpc_cidr}"
    instance_tenancy = "default"

    enable_dns_hostnames = true
    enable_dns_support = true

    lifecycle {
        prevent_destroy = true
    }

    tags {
        Name = "${var.vpc_name}_vpc"
    }
}

# Internet Gateway
resource "aws_internet_gateway" "internet_gateway" {
    vpc_id = "${aws_vpc.vpc.id}"

    tags {
        Name = "${var.vpc_name}_igw"
    }
}

# for each availability zone, create a public and private subnet, then create
# an EIP, attach a aws_nat_gateway to each, and an aws_route_table. Each nat
# needs a dedicated EIP since nats live in one availability zone.

# Public Subnets
resource "aws_subnet" "public" {
    vpc_id = "${aws_vpc.vpc.id}"
    cidr_block = "${element(var.public_subnets, count.index)}"
    availability_zone = "${element(var.availability_zones, count.index)}"
    count = "${length(var.public_subnets)}"
    map_public_ip_on_launch = true

    lifecycle {
        prevent_destroy = true
    }

    tags {
        Name = "${format("%s.external.%s", var.vpc_name, element(var.availability_zones, count.index))}"
    }
}

# Private Subnets
resource "aws_subnet" "private" {
    vpc_id = "${aws_vpc.vpc.id}"
    cidr_block = "${element(var.private_subnets, count.index)}"
    availability_zone = "${element(var.availability_zones, count.index)}"
    count = "${length(var.private_subnets)}"

    lifecycle {
        prevent_destroy = true
    }

    tags {
        Name = "${format("%s.internal.%s", var.vpc_name, element(var.availability_zones, count.index))}"
    }
}

# Create an EIP for each NAT gateway, since each gateway lives in it's own
# availability zone.
resource "aws_eip" "nat" {
    count = "${length(var.public_subnets)}"
    vpc = true
}

# Setup NAT gateway
resource "aws_nat_gateway" "nat" {
    count = "${length(var.public_subnets)}"
    allocation_id = "${element(aws_eip.nat.*.id, count.index)}"
    subnet_id = "${element(aws_subnet.public.*.id, count.index)}"
    depends_on = ["aws_internet_gateway.internet_gateway"]
}

resource "aws_route_table" "public" {
    vpc_id = "${aws_vpc.vpc.id}"

    tags {
        Name = "${var.vpc_name}_public_route_table"
    }
}

# add a public gateway to each public route.
resource "aws_route" "public_gateway_route" {
    route_table_id = "${aws_route_table.public.id}"
    depends_on = ["aws_route_table.public"]
    destination_cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.internet_gateway.id}"
}

# for each of the private subnets, create a "private" route table
resource "aws_route_table" "private" {
    vpc_id = "${aws_vpc.vpc.id}"
    count = "${length(var.private_subnets)}"
    propagating_vgws = ["${var.virtual_gateway_id}"]

    tags {
        Name = "${var.vpc_name}_private_route_table_${count.index}"
    }
}

# add a nat gateway to each private subnet route.
resource "aws_route" "private_nat_gateway_route" {
    count = "${length(var.private_subnets)}"
    route_table_id = "${element(aws_route_table.private.*.id, count.index)}"
    depends_on = ["aws_route_table.private"]
    destination_cidr_block = "0.0.0.0/0"
    nat_gateway_id = "${element(aws_nat_gateway.nat.*.id, count.index)}"
}

# Associate public subnets with public route table
resource "aws_route_table_association" "public" {
    count = "${length(var.public_subnets)}"
    subnet_id = "${element(aws_subnet.public.*.id, count.index)}"
    route_table_id = "${aws_route_table.public.id}"
}

# Associate private subnets with private route table
resource "aws_route_table_association" "private" {
    count = "${length(var.private_subnets)}"
    subnet_id = "${element(aws_subnet.private.*.id, count.index)}"
    route_table_id = "${element(aws_route_table.private.*.id, count.index)}"
}


#########
# Outputs
#########
output "vpc_id" {
    value = "${aws_vpc.vpc.id}"
}

output "public_subnet_ids" {
    value = ["${aws_subnet.public.*.id}"]
}

output "private_subnet_ids" {
    value = ["${aws_subnet.private.*.id}"]
}

output "private_route_tables" {
    value = ["${aws_route_table.private.id}"]
}

output "nat_gateway_id" {
    value = "${aws_nat_gateway.nat.id}"
}
