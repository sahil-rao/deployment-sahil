# Provides common functionality and enforces standards as related
# to the provisioning of route53 records.

####################
# Required variables
####################

# We need VPC ID for private hosted zones
variable "vpc_id" {}

# Optional root name of our private hosted zone e.g cws.com
variable "zone_name" {
    default = "cws.com"
}

#########################################
# Create resources specified in variables
#########################################

# Should be only 1 internal hosted zone.
resource "aws_route53_zone" "zone" {
    name = "${var.zone_name}"
    vpc_id = "${var.vpc_id}"
}

#########
# Outputs
#########

output "zone_id" {
    value = "${aws_route53_zone.zone.zone_id}"
}

output "zone_name" {
    value = "${var.zone_name}"
}
