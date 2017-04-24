# This file is not part of the actual build process and is meant as a utility.

TOP := $(realpath .)
VENV_DIR = $(TOP)/target

all: setup-pip

venv:
	virtualenv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install pip-tools

requirements.txt: venv requirements.in
	$(VENV_DIR)/bin/pip-compile

setup-pip: requirements.txt
	$(VENV_DIR)/bin/pip install -r requirements.txt
	$(VENV_DIR)/bin/pip install -e .

clean:
	rm -rf $(VENV_DIR)
