PYTHON := .venv/bin/python
SRC := src
export PYTHONPATH := $(SRC)

.PHONY: install lint typecheck test check run

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m flake8 $(SRC) tests

typecheck:
	$(PYTHON) -m mypy --strict -p library

test:
	$(PYTHON) -m pytest tests

check: lint typecheck test

run:
	$(PYTHON) -m library
