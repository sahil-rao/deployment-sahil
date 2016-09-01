variable "region" {}
variable "distribution" {}
variable "architecture" {
    default = "x86_64"
}
variable "virttype" {}

variable "all_amis" {
    default = {
        "us-east-1-nodejs-6.2.0-0-x86_64-hvm" = "ami-070de66a"
        "us-west-1-nodejs-6.2.0-0-x86_64-hvm" = "ami-15b4cc75"
        "us-west-2-nodejs-6.2.0-0-x86_64-hvm" = "ami-e98f7089"
    }
}

output "ami_id" {
    value = "${lookup(var.all_amis, format(\"%s-%s-%s-%s\", var.region, var.distribution, var.architecture, var.virttype))}"
}
