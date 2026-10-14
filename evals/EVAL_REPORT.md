# CodeSentinel AI Evaluation Report

Evaluation benchmark assessing automated PR finding detection and issue triage classification accuracy across Python, TypeScript, Go, and Rust.

## Summary Metrics

| Metric | Value | Target |
|---|---|---|
| **Total Evaluated Samples** | 12 | >= 10 |
| **Fully Passed (100% Match)** | 12/12 (100.0%) | - |
| **True Positives (TP)** | 23 | - |
| **False Positives (FP)** | 0 | - |
| **False Negatives (FN)** | 0 | - |
| **Precision** | **1.000** (100.0%) | >= 0.85 |
| **Recall** | **1.000** (100.0%) | >= 0.85 |
| **F1 Score** | **1.000** | >= 0.85 |

## Detailed Evaluation Results

| ID | Type | Language | Title | Expected | Predicted | Status |
|---|---|---|---|---|---|---|
| `PR-PY-01` | PR | python | SQL Injection in User Search | `sql-injection, security` | `sql-injection, security` | PASS |
| `PR-PY-02` | PR | python | Hardcoded AWS Access Key in Client | `hardcoded-secret, security` | `hardcoded-secret, security` | PASS |
| `ISS-PY-03` | ISSUE | python | Crash with 500 when Authorization header is missing | `bug, security` | `bug, security` | PASS |
| `PR-TS-04` | PR | typescript | Command Injection in Image Converter | `command-injection, security` | `command-injection, security` | PASS |
| `PR-TS-05` | PR | typescript | Exposed API Key in Client Config | `hardcoded-secret, security` | `hardcoded-secret, security` | PASS |
| `ISS-TS-06` | ISSUE | typescript | Add dark mode theme toggle to web console | `enhancement, ui` | `enhancement, ui` | PASS |
| `PR-GO-07` | PR | go | SQL Injection via fmt.Sprintf in User Query | `sql-injection, security` | `sql-injection, security` | PASS |
| `PR-GO-08` | PR | go | Goroutine Resource Leak in Worker Pool | `resource-leak, bug` | `resource-leak, bug` | PASS |
| `ISS-GO-09` | ISSUE | go | Panic: runtime error: invalid memory address or nil pointer dereference in Router.ServeHTTP | `bug` | `bug` | PASS |
| `PR-RS-10` | PR | rust | Command Injection via Shell Execution in Runner | `command-injection, security` | `command-injection, security` | PASS |
| `PR-RS-11` | PR | rust | Panic Risk on unwrap in Parser | `panic-risk, bug` | `panic-risk, bug` | PASS |
| `ISS-RS-12` | ISSUE | rust | Add support for async streaming in Rust client library | `enhancement, performance` | `enhancement, performance` | PASS |
