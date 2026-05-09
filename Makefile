PYTHON ?= python

.PHONY: test lint format check
test:
	PYTHONPATH=src $(PYTHON) -m pytest -q tests

lint:
	ruff check .

format:
	ruff format .

check:
	ruff check .
	ruff format --check .
