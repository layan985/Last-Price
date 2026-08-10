.PHONY: install rebuild test api audit

install:
	python -m pip install -e ".[dev]"

rebuild:
	PYTHONPATH=src python scripts/rebuild_demo.py

test:
	PYTHONPATH=src pytest

api:
	PYTHONPATH=src uvicorn last_price.api:app --reload

audit:
	PYTHONPATH=src python -m last_price.cli audit
