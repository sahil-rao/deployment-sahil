TOP := $(realpath .)
VENV_DIR = $(TOP)/venv

all: setup-pip

venv:
	virtualenv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip==9.0.1 # needed for pip-tools<1.7
	$(VENV_DIR)/bin/pip install pip-tools

requirements.txt: venv requirements.in
	$(VENV_DIR)/bin/pip-compile

setup-pip: requirements.txt
	$(VENV_DIR)/bin/pip install -r requirements.txt

.PHONY: test
test:
	$(VENV_DIR)/bin/py.test test unittests

clean:
	rm -rf $(VENV_DIR)
