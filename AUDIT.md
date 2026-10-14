# CodeSentinel AI ? Phase 0 Comprehensive Audit & Shared Contracts

**Date:** October 14, 2026  
**Environment:** Remote Linux VM (`student@192.168.123.133`), Python 3.14 / 3.12, Node.js v20.20.2  
**Target Repos:** `kushmunjal/codesentinel-ai`, `kushmunjal/codesentinel-test`, `kushmunjal/filecoin-pay-explorer`  
**Current Branch:** `phase0/audit-and-contracts`

---

## 1. Executive Summary

A comprehensive architectural and functional audit of CodeSentinel AI was conducted across the core pipeline, the FastAPI/SQLite backend, the React console, the evaluation harness, and live GitHub CI workflows.

While the foundational pipelines for PR review and issue triage function against happy-path repositories, the system currently exhibits critical reliability gaps in CI environments (e.g., Dependabot/unauthenticated forks), lacks idempotency on PR/issue updates, leaks raw code containing secrets to third-party LLMs before redacting, uses a naive 4-word overlap for duplicate detection, runs without authentication or rate-limiting on the console API, and lacks formal automated migrations, security scanning, and Prometheus observability.

All Groq model IDs have been verified live against the Groq API, and strict shared contracts (Config, DB, API schemas, Metrics) have been implemented and validated before launching parallel workstreams.

---

## 2. Groq Model Verification & Configuration

Live call to `https://api.groq.com/openai/v1/models` using the configured API key returned:
- `qwen/qwen3.8-27b` (Active primary model ? confirmed valid and operational)
- `openai/gpt-oss-120b` (Active fallback model ? confirmed valid and operational)
- `openai/gpt-oss-20b` (Confirmed valid)
- `meta-llama/llama-prompt-guard-2-86m` (Available for guardrail integration)

**Configuration Contract (`src/codesentinel/config.py`):**
- Primary model, fallback model, base URL, and provider are fully configurable via `.codesentinel.yml` with direct override via environment variables:
  - `MODEL` (default: `qwen/qwen3.8-27b`)
  - `FALLBACK_MODEL` (default: `openai/gpt-oss-120b`)
  - `BASE_URL` (default: `https://api.groq.com/openai/v1`)
  - `PROVIDER` (default: `groq`)
- Strict Pydantic validation ensures missing or malformed configuration triggers clear maintainer feedback.

---

## 3. Confirmed Bugs & Root Cause Analysis

| # | Bug | Root Cause | Impact | Fix |
|---|---|---|---|---|
| **BUG-01** | Dependabot/Fork PRs Crash with Exit Code 1 | `OpenAICompatProvider.__init__` raises unhandled `ValueError("API_KEY must be set.")` when GitHub secrets are not passed (e.g. Dependabot or public forks). | CI workflow crashes on valid PRs. Observed on `filecoin-pay-explorer#14` (Run 38544566646). | Graceful degradation: Check `API_KEY` upfront. If absent, post a neutral skipped review comment, log notice, and exit 0. |
| **BUG-02** | Unit Test Suite Failure in `test_llm.py` | `test_retry_success_after_failure` mocked an outdated `PRSummary` lacking required schema fields (`risk_reasoning`, `review_effort`, `review_effort_reasoning`). | Test failed after 3 retries and 66 seconds of exponential sleep. | Fixed mock in `test_llm.py` to satisfy full Pydantic schema (suite now runs in 1.38s). |
| **BUG-03** | Duplicate Review and Triage Comments | `publish_review()` in `publish.py` and `run_triage_pipeline()` in `pipeline.py` do not verify whether a review/comment has already been submitted for the specific `head_sha` or issue body hash. | Issue #12 received 3 duplicate triage comments; multiple reviews posted on same commit. | Enforce idempotency: Key PR reviews by `(pr_number, head_sha)` and issue triage by `(issue_number, body_hash)`. |
| **BUG-04** | Secret Leakage to LLM API | `checks/secrets.py` flags detected secrets via regex, but `pipeline.py` subsequently sends the unredacted raw diff directly to the Groq API. | Sensitive credentials/tokens are transmitted across the network to external LLM providers. | Redact all detected credentials, private keys, and high-entropy secrets from the diff before tokenization and LLM transmission. |
| **BUG-05** | Naive 4-Word Duplicate Issue Detection | `duplicates.py` flags an issue as duplicate if `len(words.intersection(target_words)) >= 4`. | High false-positive rate on generic issue descriptions (e.g. issues sharing words like "when", "error", "please", "code"). | Replace with Jaccard token similarity with stop-word filtering or embedding cosine similarity with a high confidence threshold (>= 0.75). |
| **BUG-06** | Mock Evaluation Harness | `evals/run_eval.py` prints hardcoded accuracy numbers (`Precision: 0.95`) without actually evaluating `evals/dataset.jsonl`. | Zero automated measurement of review accuracy or regressions. | Build real evaluation runner that benchmarks model outputs against labeled test fixtures with precision/recall/F1 metrics. |
| **BUG-07** | Unauthenticated Console API & Missing Headers | FastAPI application defines `allow_origins=["*"]` with no JWT/session authentication, no CSRF/security headers, and no rate limiting. | Any client with network access to port 8080 can query, modify, or spam the backend. | Add token/hashed credential login, restrict CORS, add rate limiting and standard security headers. |
| **BUG-08** | SQLite Database Concurrency / Lock Risks | `codesentinel.db` initialized with default `journal_mode=DELETE` and no busy timeout. | Daemon polling and API requests concurrently touching SQLite risk `sqlite3.OperationalError: database is locked`. | Switched engine to `PRAGMA journal_mode=WAL;`, `PRAGMA busy_timeout=5000;`, and `PRAGMA foreign_keys=ON;`. |

---

## 4. Gap Analysis vs. Target Production Spec

### Workstream A: Core Reliability
- [ ] Dependabot/fork safe exit 0 when `API_KEY` is omitted.
- [ ] Secret & PII redaction pipeline before LLM calls.
- [ ] Idempotent review comments keyed by PR + head SHA.
- [ ] SHA-256 diff chunk caching to avoid redundant LLM billing.
- [ ] Model fallback chain (`qwen/qwen3.8-27b` -> `openai/gpt-oss-120b`).
- [ ] Per-run token and cost budget tracker with hard stop.
- [ ] Comprehensive `.codesentinel.yml` parser with Pydantic validation (Scaffolded in Phase 0).
- [ ] Multi-pattern and Shannon entropy-based secret scanning with allowlist.
- [ ] SARIF output generation and GitHub Check Run integration.
- [ ] FastAPI webhook endpoint with `X-Hub-Signature-256` verification.
- [ ] Improved duplicate detection and stale "needs-info" issue pinging.

### Workstream B: Security & Supply Chain
- [ ] Prompt-injection test suite and system prompt guardrails.
- [ ] Security scanners: `pip-audit`, `bandit`, `trivy`, `gitleaks`, `CodeQL`.
- [ ] Pinned dependencies with hashes, pinned GitHub Actions SHAs.
- [ ] Least-privilege `permissions:` across all workflows.
- [ ] Console authentication (hashed credentials / token session), CORS lockdown, security headers.
- [ ] `SECURITY.md` and `THREAT_MODEL.md`.

### Workstream C: DevOps & Deployment
- [ ] Multi-stage `Dockerfile` and `docker-compose.yml`.
- [ ] `systemd` service units (`codesentinel-console.service`, `codesentinel-daemon.service`) with restart policies.
- [ ] Automated VM bootstrap script (`bootstrap.sh`) for idempotent fresh-machine setup.
- [ ] `Makefile` with targets (`setup`, `lint`, `test`, `eval`, `build`, `docker`, `clean`).
- [ ] CI pipeline for `codesentinel-ai` (Ruff, Mypy, Pytest, React build, Docker build).
- [ ] Automated release workflow with semver tagging, changelog, and GHCR publishing.
- [ ] SQLite WAL mode (Implemented in Phase 0) and automated backup/restore script.

### Workstream D: Observability
- [ ] Structured JSON logging with correlation IDs (`repo`, `pr_number`, `run_id`).
- [ ] `/healthz`, `/readyz`, and Prometheus `/metrics` endpoint (Scaffolded in Phase 0).
- [ ] Grafana dashboard definition and Prometheus scrape configuration.
- [ ] Console bot performance telemetry view.

### Workstream E: Console UI/UX
- [ ] Dark/light theme with Tailwind system preference.
- [ ] Skeleton loaders, empty states, error states, and toast notifications.
- [ ] Filterable, searchable, paginated PR and Issue tables with CSV export.
- [ ] Detailed PR drawer/page with findings categorized by severity, risk score explanations, and GitHub links.
- [ ] Detailed Issue drawer with triage classification, duplicate candidates, and missing info items.
- [ ] Maintainer feedback mechanism on findings (useful / false positive) wired to API.
- [ ] Accessible WCAG AA UI and mobile layout.
- [ ] Login screen wired to backend authentication.

### Workstream F: QA & Documentation
- [ ] Core unit test coverage expanded to >= 80%.
- [ ] Integration tests with GitHub API and LLM fixtures.
- [ ] Expanded evaluation benchmark (`evals/dataset.jsonl`) with precision/recall reporting.
- [ ] Complete documentation: `README.md` rewrite (Mermaid diagrams, badges, screenshots), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `RUNBOOK.md`.
- [ ] GitHub Marketplace metadata in `action.yml`.

---

## 5. Shared Contracts (Defined & Active)

### A. Configuration Contract (`src/codesentinel/config.py`)
- Pydantic model `CodeSentinelConfig` loaded via `load_config()`.
- Validates model IDs, token budgets, cost limits, ignore paths, severity thresholds, and custom labels.

### B. Database Schema Contract (`src/codesentinel/api/database.py`)
- SQLite initialized with WAL mode, 5000ms busy timeout, and foreign keys.
- Models: `PRState`, `FindingRecord`, `IssueState`, `ActivityLog`, `User`, `CacheEntry`, `EvalMetricRecord`.
- Non-destructive automated column migrations active on startup.

### C. API Schemas Contract (`src/codesentinel/api/schemas.py`)
- Standardized Pydantic shapes for: `StatsResponse`, `PRResponse`, `PRDetailResponse`, `FindingResponse`, `IssueResponse`, `IssueDetailResponse`, `FindingFeedbackRequest`, `LoginRequest`, `TokenResponse`, `HealthResponse`, `EvalMetricResponse`.

### D. Prometheus Metrics Contract (`src/codesentinel/observability/metrics.py`)
- `codesentinel_reviews_total{repo, risk, status}`
- `codesentinel_findings_total{repo, severity, category}`
- `codesentinel_issues_triaged_total{repo, type, priority}`
- `codesentinel_llm_requests_total{model, status}`
- `codesentinel_llm_latency_seconds{model}`
- `codesentinel_llm_tokens_total{model, direction}`
- `codesentinel_llm_cost_dollars_total{model}`
- `codesentinel_cache_hits_total{cache}`
- `codesentinel_cache_misses_total{cache}`
- `codesentinel_active_reviews_count`
- `codesentinel_feedback_total{type}`

---

## 6. Workstream Ownership & Execution Plan

To prevent merge conflicts during parallel development, each workstream operates on designated directories and modules:

| Workstream | Branch | Owned Directories / Files | Primary Deliverables |
|---|---|---|---|
| **WS-A: Core Reliability** | `ws/core` | `src/codesentinel/review/`, `src/codesentinel/triage/`, `src/codesentinel/checks/`, `src/codesentinel/llm/` | Fork/Dependabot exit 0, secret redaction, idempotency, chunk caching, fallback model chain, SARIF output, Check Runs. |
| **WS-B: Security & Supply Chain** | `ws/security` | `tests/security/`, `SECURITY.md`, `THREAT_MODEL.md`, `src/codesentinel/api/auth.py` | Prompt injection suite, console auth, CORS lockdown, security headers, Bandit/Trivy/Gitleaks configs. |
| **WS-C: DevOps & Deployment** | `ws/devops` | `Dockerfile`, `docker-compose.yml`, `systemd/`, `bootstrap.sh`, `Makefile`, `.github/workflows/` | Containerization, systemd units, VM bootstrap, CI workflows with Ruff/Mypy/Pytest, release pipeline. |
| **WS-D: Observability** | `ws/observability` | `src/codesentinel/observability/`, `src/codesentinel/api/main.py` (metrics/health endpoints), `monitoring/` | Prometheus `/metrics`, `/healthz`, `/readyz`, structured JSON logging, Grafana dashboard JSON. |
| **WS-E: Console UI/UX** | `ws/ui` | `console/src/` | Auth UI, dark/light theme, filters, pagination, CSV export, PR/issue drawers, finding feedback, mobile responsiveness. |
| **WS-F: QA & Docs** | `ws/qa` | `tests/unit/`, `tests/integration/`, `evals/`, `README.md`, `docs/`, `action.yml` | >= 80% coverage, real eval runner with precision/recall, Playwright MCP e2e test suite, docs rewrite. |

**Integration:**
Following workstream completion, an integrator merges branches into `main` sequentially, resolves any inter-module dependencies, runs the end-to-end Phase 12 validation suite and Playwright tests, and generates `FINAL_REPORT.md`.
