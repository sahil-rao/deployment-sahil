module "ecs" {
    source = "../../modules/ecs"

    name = "ecs"
    version = 4

    vpc_id = "${data.terraform_remote_state.networking.vpc_id}"
    subnet_ids = ["${data.terraform_remote_state.networking.private_subnet_ids}"]

    key_name = "${var.key_name}"
    instance_type = "t2.medium"
    min_size = 12
    max_size = 30
    desired_capacity = 12
}
