# Phase 2 ? Repo Skeleton + Dashboard Skeleton

**What was done:**
- Created repository skeleton for the GitHub Action (ction.yml, src/codesentinel/main.py, .github/workflows/ci.yml).
- Added FastAPI and uvicorn dependencies in pyproject.toml, alongside dev dependencies pytest and 
uff.
- Built the dashboard skeleton in dashboard/ with a styled dark theme HTML layout using Tailwind and Mermaid.js.
- Started the dashboard in a detached 	mux session on 127.0.0.1:8080.

**Exact commands run:**
- Scaffolded directory structure and created stub files.
- pip install -e .[dev] to install FastAPI, uvicorn, pytest, and ruff.
- 	mux new-session -d -s dashboard "cd ~/codesentinel-ai && source .venv/bin/activate && uvicorn dashboard.app:app --host 127.0.0.1 --port 8080"

**Proof of completion:**
- curl http://127.0.0.1:8080 locally on the VM returns the Dashboard HTML.
- Tmux session dashboard is running.
- Directory tree includes all requested files.

**What changed in the dashboard:**
The entire skeleton was created. It contains the Hero section, placeholders for PR Review, Issue Triage, and Evaluation, a real Architecture diagram, and the Build Progress list with Phases 1 and 2 checked off.

**How to start/stop the dashboard:**
- Start (or re-attach): 	mux attach -t dashboard (to view) or 	mux new-session -d -s dashboard "cd ~/codesentinel-ai && source .venv/bin/activate && uvicorn dashboard.app:app --host 127.0.0.1 --port 8080" (to start in background).
- Stop cleanly: 	mux kill-session -t dashboard

**How to view locally:**
Run this command from your host machine:
\ssh -L 8080:localhost:8080 student@192.168.123.133\
Then open \http://localhost:8080\ in your browser.

**What's left for the next phase:**
Phase 3: PR diff pipeline (Fetch, Filter, Chunk, Line Mapping) and writing unit tests.
