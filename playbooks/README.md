# Navigator Optimizer Ansible Scripts

These ansible scripts setup Navigator Optimizer inside an account. They can be
run by going into one of the account directories and running the ansible
scripts that drive the account configuration.

In order to use these scripts, first you must install the necessary
dependencies. The `Makefile` drives all of this and can be installed simply by
just running:

```shell
% make
```

Next, you will need the passwords for each environment. Talk to SRE, then put
the files into `$HOME/.navopt/$ENV/vault_pass`.

# Running the scripts.

For example, the following command will do a dry-run for upgrading the
Backoffice machines inside the dev-us-west-2 AWS account:

```shell
% ./run-ansible-playbook dev \
    --limit tag_Name_Backoffice \
    --extra-vars "BuildVersion=erickt/master/" \
    --check
...
```

When we want to actually do a release, we can remove the `--check`:

```shell
% ./run-ansible-playbook dev \
    --limit tag_Name_Backoffice \
    --extra-vars "BuildVersion=erickt/master/"
```

Typically a release is comprised of the UI, the backoffice, and the admin
server. These can be installed with the prior command and with:

```shell
# Release the frontend
% ./run-ansible-playbook dev \
    --limit tag_Name_NodeJS \
    --extra-vars "BuildVersion=erickt/master/"

...

# Release the backoffice
% ./run-ansible-playbook dev \
    --limit tag_Name_AdminServer \
    --extra-vars "BuildVersion=erickt/master/"
...
```

# Changing secrets

Passwords are encrypted with [ansible-vault](http://docs.ansible.com/ansible/playbooks_vault.html).
There is a helper script to simplify editing this file:

```shell
% ./edit-secrets dev
```
