VENV := venv
PYTHON := $(VENV)/bin/python
RM := rm -rf

venv:
	$(RM) $(VENV)
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -U pip wheel setuptools
	$(PYTHON) -m pip install -U git+https://github.com/uNickz/WebSite2PDF
	@echo "Created venv with $$($(PYTHON) --version)"

api:
	cd Example/ && ../$(PYTHON) example.py