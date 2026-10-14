.PHONY: all setup lint typecheck test eval build run docker clean help

PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
RUFF ?= .venv/bin/ruff
PYTEST ?= .venv/bin/pytest
UVICORN ?= .venv/bin/uvicorn

all: lint test

setup:
	@echo "==> Setting up environment..."
	./bootstrap.sh

lint:
	@echo "==> Running Python lint (ruff)..."
	$(RUFF) check .
	@echo "==> Running Console lint..."
	cd console && npm run lint

typecheck:
	@echo "==> Typechecking Console frontend..."
	cd console && npm run build
	@echo "==> Typechecking Python backend..."
	@if [ -f .venv/bin/mypy ]; then .venv/bin/mypy src --ignore-missing-imports || true; else echo "mypy not installed, skipping backend typecheck"; fi

test:
	@echo "==> Running pytest test suite..."
	$(PYTEST) --cov=codesentinel --cov-report=term tests/

eval:
	@echo "==> Running evaluation benchmark..."
	$(PYTHON) evals/run_eval.py

build:
	@echo "==> Building Console frontend..."
	cd console && npm run build
	@echo "==> Building Python package..."
	$(PIP) install -e . --quiet

run:
	@echo "==> Starting CodeSentinel Console API server..."
	$(UVICORN) codesentinel.api.main:app --host 0.0.0.0 --port 8080

docker:
	@echo "==> Building Docker image..."
	docker build -t codesentinel:latest .

clean:
	@echo "==> Cleaning build and cache artifacts..."
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .coverage htmlcov console/dist
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
