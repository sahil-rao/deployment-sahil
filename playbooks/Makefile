TOP := $(realpath .)
VENV_DIR = $(TOP)/venv

all: setup-pip setup-ansible

venv:
	virtualenv $(VENV_DIR)
#	$(VENV_DIR)/bin/pip install --upgrade pip==8.1.1 # needed for pip-tools<1.7
	$(VENV_DIR)/bin/pip install pip-tools

requirements.txt: venv requirements.in
	$(VENV_DIR)/bin/pip-compile

setup-pip: requirements.txt
	$(VENV_DIR)/bin/pip install -r requirements.txt

setup-ansible: setup-pip requirements.yml
	$(VENV_DIR)/bin/ansible-galaxy install -r requirements.yml -p venv/etc/ansible

clean:
	rm -rf $(VENV_DIR)
