PYTHON ?= python

.PHONY: test
test:
	PYTHONPATH=src $(PYTHON) -m pytest -q tests
