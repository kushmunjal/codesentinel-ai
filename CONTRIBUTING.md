# Contributing to CodeSentinel AI

Thank you for your interest in contributing to CodeSentinel AI! We welcome contributions that help improve PR reviews, issue triage, and developer workflow automation.

---

## ?? Core Philosophy: Ponytail Engineering

CodeSentinel AI follows strict **Ponytail engineering principles**:
1. **Standard Library First**: Prefer native Python libraries (`json`, `re`, `urllib`, `sqlite3`, `pathlib`) before reaching for third-party dependencies.
2. **Minimal & Clean Code**: One clean line is better than fifty lines of unnecessary abstraction. Resist over-engineering, enterprise boilerplate, and premature design patterns.
3. **Fail-Safe & Predictable**: Automation in production repositories must fail gracefully and never block developer merges on transient network glitches.
4. **Secret Safety**: Under no circumstance should tokens, API keys, credentials, or `.env` files be logged or committed.

---

## ??? Development Setup

### Prerequisites
- **Python 3.12+**
- **Node.js 20+** (for web console and Vite frontend)
- **Git**

### Local Setup Steps

1. **Clone the repository and set up a virtual environment**:
   ```bash
   git clone https://github.com/kushmunjal/codesentinel-ai.git
   cd codesentinel-ai
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e ".[dev]"
   pip install pytest-cov playwright
   ```

2. **Install frontend console dependencies**:
   ```bash
   cd console
   npm install
   npm run build
   cd ..
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your local or test API credentials (LLM_API_KEY, GITHUB_TOKEN)
   ```

---

## ?? Testing Guidelines

All contributions must include test coverage. We enforce a minimum **>= 80% test coverage** on core modules.

### Running Unit Tests
```bash
pytest tests/unit/ --cov=codesentinel --cov-report=term-missing
```

### Running Integration Tests
```bash
pytest tests/integration/ -v
```

### Running E2E Console Tests
```bash
pytest tests/e2e/ -v
```

### Running the Evaluation Harness
Verify detector accuracy and triage classification across multi-language PRs:
```bash
python evals/run_eval.py
```

### Linting and Code Style
```bash
ruff check src/ tests/
cd console && npm run lint && cd ..
```

---

## ?? Git & Pull Request Workflow

1. **Create a branch**:
   Use meaningful branch names:
   - `feat/feature-name`
   - `fix/bug-description`
   - `docs/documentation-update`
   - `qa/test-coverage-expansion`

2. **Commit Message Conventions**:
   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(review): add AST-based query parameter check`
   - `fix(positions): correctly map multiline hunk offsets`
   - `docs(readme): update configuration matrix`
   - `test(e2e): add test coverage for /eval route`

3. **Submitting your PR**:
   - Ensure all `pytest` suites pass locally.
   - Run `evals/run_eval.py` to confirm no regression in evaluation precision/recall.
   - Verify that no untracked secrets or credentials exist in `git status`.
   - Provide a clear PR description explaining the changes and linking relevant issues.
