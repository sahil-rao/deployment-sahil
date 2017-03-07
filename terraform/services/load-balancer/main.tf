data "aws_ami" "ubuntu_ami" {
    most_recent = true
    filter {
        name = "name"
        values = ["ubuntu/images/hvm-ssd/ubuntu-trusty-14.04-amd64-server-20170202.1"]
    }
    owners = ["099720109477"]
}

resource "aws_instance" "default" {
    ami = "${data.aws_ami.ubuntu_ami.id}"
    vpc_security_group_ids = ["${aws_security_group.nginx.id}"]
    subnet_id = "${element(var.subnet_ids, count.index)}"
    key_name = "${var.key_name}"

    iam_instance_profile = "${aws_iam_instance_profile.nginx.name}"

    # FIXME: This is what's used in production.
    # instance_type = "m4.xlarge"
    instance_type = "${var.instance_type}"
    ebs_optimized = "${var.ebs_optimized}"

    tags {
        Cluster = "${var.env}"
        Environment = "${var.env}"
        Name = "${var.name}"
    }
}

output "instance_id" {
    value = "${aws_instance.default.id}"
}
