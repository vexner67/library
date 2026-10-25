PYTHON := .venv/bin/python
SRC := src
export PYTHONPATH := src/library
export MYPYPATH := src/library

.PHONY: install lint typecheck test check run

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m flake8 $(SRC) tests

typecheck:
	$(PYTHON) -m mypy --strict --explicit-package-bases $(SRC)/library

test:
	$(PYTHON) -m pytest tests

check: lint typecheck test

run:
	PYTHONPATH=src/library .venv/bin/python src/library/__main__.py
