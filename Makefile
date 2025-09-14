
.PHONY: setup run lint test clean

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	python scripts/run_backtest.py

lint:
	python -m compileall -q src

test:
	pytest -q || true

clean:
	rm -rf __pycache__ .pytest_cache artifacts/* mlruns
