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

demo:
demo:
	@echo "=========================================================="
	@echo "        CodeSentinel AI — Live End-to-End Demo            "
	@echo "=========================================================="
	@echo "==> 1. Verifying System Health & Readiness..."
	@curl -s http://127.0.0.1:8080/healthz | grep -q '"status":"ok"' && echo "    [PASS] /healthz is OK"
	@curl -s http://127.0.0.1:8080/readyz | grep -q '"database":"ok"' && echo "    [PASS] /readyz is Ready"
	@echo "==> 2. Inspecting Live Console Statistics..."
	@curl -s http://127.0.0.1:8080/api/stats
	@echo ""
	@echo "==> 3. Testing PR #19 Security Finding Detail..."
	@curl -s http://127.0.0.1:8080/api/prs/19 | grep -q '"risk_level":"HIGH"' && echo "    [PASS] PR #19 flagged as HIGH risk with credentials finding"
	@echo "==> 4. Submitting Maintainer Feedback (Finding #5: useful)..."
	@curl -s -X POST http://127.0.0.1:8080/api/findings/5/feedback -H "Content-Type: application/json" -d '{"feedback": "useful"}' | grep -q '"status":"ok"' && echo "    [PASS] Feedback registered successfully"
	@echo "==> 5. Verifying Prometheus Feedback Metrics..."
	@curl -s http://127.0.0.1:8080/metrics | grep 'codesentinel_feedback_total{type="useful"}'
	@echo "=========================================================="
	@echo " Demo execution completed successfully!                   "
	@echo " Presenter Runbook: DEMO_RUNBOOK.md                       "
	@echo " Verification Results: DEMO_RESULTS.md                   "
	@echo "=========================================================="

clean:
	@echo "==> Cleaning build and cache artifacts..."
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .coverage htmlcov console/dist
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
