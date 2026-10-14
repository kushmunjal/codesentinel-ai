# CodeSentinel AI Operations Runbook

This operations runbook outlines production deployment procedures, database backup routines, failure recovery playbooks, and monitoring health checks for CodeSentinel AI.

---

## ??? System Architecture & Services

CodeSentinel AI consists of three operational components:
1. **GitHub Action Runner / Webhook Consumer**: Executes diff analysis, heuristic and secret checks, LLM chunk review, and triage pipelines on GitHub events (`pull_request`, `issues`).
2. **FastAPI Management API**: Serves JSON APIs (`/api/health`, `/api/stats`, `/api/prs`, `/api/issues`), Prometheus telemetry metrics (`/metrics`), and SPA bundle assets.
3. **SQLite Operational Database (WAL Mode)**: High-concurrency relational store storing PR states, inline findings, triage issue states, and benchmark metric history.

---

## ?? Deployment Instructions

### 1. Systemd Service Deployment (Recommended for VM/Host)

Create systemd service file at `/etc/systemd/system/codesentinel.service`:
```ini
[Unit]
Description=CodeSentinel AI Management Console & API
After=network.target

[Service]
Type=simple
User=student
WorkingDirectory=/home/student/worktrees/ws-qa
Environment="PATH=/home/student/worktrees/ws-qa/.venv/bin:/usr/bin"
Environment="DATABASE_PATH=/home/student/codesentinel-ai/codesentinel.db"
ExecStart=/home/student/worktrees/ws-qa/.venv/bin/uvicorn codesentinel.api.main:app --host 0.0.0.0 --port 8080 --workers 2
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable codesentinel.service
sudo systemctl start codesentinel.service
sudo systemctl status codesentinel.service
```

### 2. Standalone Direct Execution
```bash
source .venv/bin/activate
uvicorn codesentinel.api.main:app --host 127.0.0.1 --port 8080
```

---

## ?? Database Management & Backup Procedures

CodeSentinel uses SQLite in **Write-Ahead Logging (WAL)** mode. Never copy `codesentinel.db` directly while write transactions are active.

### Online SQLite Backup Routine
Execute an online backup via the SQLite CLI `.backup` command or API to guarantee point-in-time consistency:
```bash
# Set variables
BACKUP_DIR="/var/backups/codesentinel"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

# Perform online non-blocking backup
sqlite3 /home/student/codesentinel-ai/codesentinel.db ".backup '${BACKUP_DIR}/codesentinel_${TIMESTAMP}.db'"

# Retain 14 days of historical backups
find "$BACKUP_DIR" -name "codesentinel_*.db" -mtime +14 -delete
```

### WAL Checkpoint Verification
To flush WAL pages back into the main database:
```bash
sqlite3 /home/student/codesentinel-ai/codesentinel.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

---

## ?? Failure Recovery Playbooks

### Playbook 1: GitHub API Rate Limiting (HTTP 403 / 429)
**Symptom**: Pipeline logs show `403 Forbidden` or `SecondaryRateLimitExceeded`.
**Resolution**:
1. Check GitHub Token rate limit status:
   ```bash
   curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```
2. Switch to a dedicated GitHub App installation token or secondary personal access token with `repo` scope.
3. Configure `RATE_LIMIT_DELAY` or adjust webhook concurrency in workflow settings.

### Playbook 2: LLM Provider Outage or Rate Limits (HTTP 429 / 503)
**Symptom**: Review chunk fails with API error or timeouts from primary provider (e.g. Groq / OpenAI).
**Resolution**:
- CodeSentinel automatically retries with exponential backoff using `generate_with_retry`.
- If the primary model continues failing, set the `FALLBACK_MODEL` in `.codesentinel.yml` or workflow inputs:
  ```yaml
  with:
    model: 'qwen/qwen3.8-27b'
    fallback_model: 'openai/gpt-oss-120b'
  ```

### Playbook 3: Corrupted SQLite Database Recovery
**Symptom**: Application logs show `sqlite3.DatabaseError: file is not a database` or `database disk image is malformed`.
**Resolution**:
1. Stop the console service:
   ```bash
   sudo systemctl stop codesentinel
   ```
2. Dump valid records and rebuild:
   ```bash
   cd /home/student/codesentinel-ai
   sqlite3 codesentinel.db ".recover" | sqlite3 codesentinel_recovered.db
   mv codesentinel.db codesentinel.db.corrupt.$(date +%s)
   mv codesentinel_recovered.db codesentinel.db
   ```
3. Initialize tables and verify integrity:
   ```bash
   sqlite3 codesentinel.db "PRAGMA integrity_check;"
   python3 -c "from codesentinel.api.database import init_db; init_db()"
   sudo systemctl start codesentinel
   ```

---

## ?? Observability & Health Checks

### Liveness Probe
```bash
curl -f -s http://127.0.0.1:8080/api/health | jq .
# Expected output: {"status": "ok"}
```

### Summary Statistics
```bash
curl -s http://127.0.0.1:8080/api/stats | jq .
```

### Prometheus Telemetry Metrics
```bash
curl -s http://127.0.0.1:8080/metrics
```
Monitored metric names:
- `codesentinel_reviews_total{repo="...", risk="...", status="..."}`
- `codesentinel_findings_total{repo="...", severity="...", category="..."}`
- `codesentinel_issues_triaged_total{repo="...", type="...", priority="..."}`
- `codesentinel_llm_latency_seconds_bucket{model="..."}`
- `codesentinel_llm_cost_dollars_total{model="..."}`
