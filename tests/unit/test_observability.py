import asyncio
import json
import logging
from unittest.mock import MagicMock, patch

from codesentinel.api.main import app, healthz, readyz
from codesentinel.observability import (
    ACTIVE_REVIEWS_GAUGE,
    CACHE_HITS_TOTAL,
    CACHE_MISSES_TOTAL,
    ISSUES_TRIAGED_TOTAL,
    LLM_LATENCY_SECONDS,
    REVIEWS_TOTAL,
    CorrelationAdapter,
    JSONFormatter,
    get_logger,
    get_metrics_summary,
)


# Helper for ASGI requests without external testclient dependencies
async def asgi_get(path: str):
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
    }
    body = []
    status = [0]
    headers = {}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            status[0] = msg["status"]
            for k, v in msg.get("headers", []):
                headers[k.decode().lower()] = v.decode()
        elif msg["type"] == "http.response.body":
            body.append(msg.get("body", b""))

    await app(scope, receive, send)
    return status[0], b"".join(body), headers


# --- 1. Structured JSON Logging Tests ---

def test_json_formatter_output():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="Pull request analyzed",
        args=(),
        exc_info=None,
    )
    record.repo = "owner/my-repo"
    record.pr_number = 101
    record.issue_number = None
    record.run_id = "run-uuid-001"
    record.risk = "high"

    output = formatter.format(record)
    data = json.loads(output)

    assert data["level"] == "INFO"
    assert data["message"] == "Pull request analyzed"
    assert data["repo"] == "owner/my-repo"
    assert data["pr_number"] == 101
    assert data["issue_number"] is None
    assert data["run_id"] == "run-uuid-001"
    assert data["risk"] == "high"
    assert "timestamp" in data


def test_json_formatter_exception_logging():
    formatter = JSONFormatter()
    try:
        raise ValueError("Something failed")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname=__file__,
        lineno=60,
        msg="Error during execution",
        args=(),
        exc_info=exc_info,
    )
    output = formatter.format(record)
    data = json.loads(output)

    assert data["level"] == "ERROR"
    assert data["message"] == "Error during execution"
    assert "exception" in data
    assert "ValueError: Something failed" in data["exception"]


def test_get_logger_and_correlation_adapter():
    logger = get_logger(
        "test.subsystem",
        repo="codesentinel/core",
        pr_number=55,
        issue_number=12,
        run_id="run-xyz",
    )
    assert isinstance(logger, CorrelationAdapter)
    assert logger.extra["repo"] == "codesentinel/core"
    assert logger.extra["pr_number"] == 55
    assert logger.extra["issue_number"] == 12
    assert logger.extra["run_id"] == "run-xyz"


# --- 2. Observability Endpoints Tests ---

def test_healthz_direct():
    result = healthz()
    assert result == {"status": "ok"}


def test_healthz_asgi():
    status, body, _ = asyncio.run(asgi_get("/healthz"))
    assert status == 200
    data = json.loads(body.decode())
    assert data == {"status": "ok"}


def test_readyz_success_direct():
    result = readyz()
    assert isinstance(result, dict)
    assert result["status"] == "ready"
    assert result["database"] == "ok"
    assert result["model_config"] == "ok"


def test_readyz_asgi():
    status, body, _ = asyncio.run(asgi_get("/readyz"))
    assert status == 200
    data = json.loads(body.decode())
    assert data["status"] == "ready"
    assert data["database"] == "ok"
    assert data["model_config"] == "ok"


def test_readyz_db_failure():
    with patch("codesentinel.api.main.engine.connect", side_effect=Exception("DB Connection refused")):
        status, body, _ = asyncio.run(asgi_get("/readyz"))
        assert status == 503
        data = json.loads(body.decode())
        assert data["status"] == "not_ready"
        assert "Connection refused" in data["database"]


def test_readyz_config_failure():
    with patch("codesentinel.api.main.load_config", side_effect=Exception("Invalid config file")):
        status, body, _ = asyncio.run(asgi_get("/readyz"))
        assert status == 503
        data = json.loads(body.decode())
        assert data["status"] == "not_ready"
        assert "Invalid config file" in data["model_config"]


def test_metrics_endpoint_asgi():
    status, body, headers = asyncio.run(asgi_get("/metrics"))
    assert status == 200
    assert "text/plain" in headers.get("content-type", "")
    content = body.decode()
    assert "codesentinel_reviews_total" in content
    assert "codesentinel_findings_total" in content


def test_api_metrics_summary_endpoint():
    status, body, _ = asyncio.run(asgi_get("/api/metrics/summary"))
    assert status == 200
    data = json.loads(body.decode())
    assert "reviews_count" in data
    assert "error_rate" in data
    assert "cache_hit_rate" in data
    assert "token_counts" in data
    assert "prompt" in data["token_counts"]
    assert "completion" in data["token_counts"]
    assert "total" in data["token_counts"]
    assert "avg_latency" in data


# --- 3. Metrics Increment & Summary Calculations ---

def test_metrics_recording_and_summary():
    REVIEWS_TOTAL.labels(repo="test/repo", risk="low", status="success").inc()
    CACHE_HITS_TOTAL.labels(cache="diff").inc(4)
    CACHE_MISSES_TOTAL.labels(cache="diff").inc(1)
    LLM_LATENCY_SECONDS.labels(model="test-model").observe(1.2)

    summary = get_metrics_summary()
    assert summary["reviews_count"] >= 1
    assert summary["cache_hit_rate"] > 0
    assert summary["avg_latency"] > 0

    # Gauge test
    initial_gauge = ACTIVE_REVIEWS_GAUGE._value.get()
    ACTIVE_REVIEWS_GAUGE.inc()
    assert ACTIVE_REVIEWS_GAUGE._value.get() == initial_gauge + 1
    ACTIVE_REVIEWS_GAUGE.dec()
    assert ACTIVE_REVIEWS_GAUGE._value.get() == initial_gauge


# --- 4. Pipeline Observability Integration Tests ---

@patch("codesentinel.review.pipeline.json.dump")
@patch("codesentinel.review.pipeline.publish_review")
@patch("codesentinel.review.pipeline.publish_summary")
@patch("codesentinel.review.pipeline.get_repo_config", return_value={"verbosity": "detailed"})
@patch("codesentinel.review.pipeline.OpenAICompatProvider")
@patch("codesentinel.review.pipeline.generate_with_retry")
@patch("codesentinel.review.pipeline.chunk_diff", return_value=["dummy chunk"])
@patch("codesentinel.review.pipeline.filter_diff", return_value="+++ b/file.py\n+dummy")
@patch("codesentinel.review.pipeline.fetch_pr_diff", return_value="+++ b/file.py\n+dummy")
@patch("codesentinel.review.pipeline.GitHubClient")
def test_review_pipeline_metrics(
    mock_gh, mock_fetch, mock_filter, mock_chunk, mock_generate,
    mock_llm_cls, mock_repo_config, mock_pub_sum, mock_pub_rev, mock_dump
):
    from codesentinel.review.pipeline import run_pipeline
    from codesentinel.schemas import Finding, PRSummary, ReviewResult

    mock_llm_instance = MagicMock()
    mock_llm_instance.model = "mock-model"
    mock_llm_cls.return_value = mock_llm_instance

    client_instance = MagicMock()
    pr_response = MagicMock()
    pr_response.json.return_value = {"body": "PR description", "head": {"sha": "sha123"}}
    client_instance.get.return_value = pr_response
    client_instance.get_file_content.return_value = None
    mock_gh.return_value = client_instance

    finding = Finding(file="file.py", line=1, severity="critical", category="security", explanation="leak")
    review_res = ReviewResult(findings=[finding])
    summary_res = PRSummary(summary="Fix", risk_level="high", risk_reasoning="Critical leak", review_effort=1, review_effort_reasoning="Easy")

    mock_generate.side_effect = [review_res, summary_res]

    import builtins
    orig_open = builtins.open
    def safe_open(file, mode="r", *args, **kwargs):
        if "w" in mode and "dashboard" in str(file):
            from unittest.mock import mock_open
            return mock_open()()
        return orig_open(file, mode, *args, **kwargs)

    with patch("builtins.open", side_effect=safe_open):
        run_pipeline("testowner", "testrepo", 99)

    summary = get_metrics_summary()
    assert summary["reviews_count"] >= 1


@patch("codesentinel.triage.pipeline.is_issue_already_triaged", return_value=False)
@patch("codesentinel.triage.pipeline.GitHubClient")
@patch("codesentinel.triage.pipeline.OpenAICompatProvider")
@patch("codesentinel.triage.pipeline.generate_with_retry")
def test_triage_pipeline_metrics(mock_generate, mock_llm_cls, mock_gh, mock_triaged):
    from codesentinel.schemas import TriageResult
    from codesentinel.triage.pipeline import run_triage_pipeline

    mock_llm_instance = MagicMock()
    mock_llm_instance.model = "mock-model"
    mock_llm_cls.return_value = mock_llm_instance

    client_instance = MagicMock()
    client_instance.get_issue.return_value = {"number": 12, "title": "Crash on login", "body": "Steps: ..."}
    client_instance.get_labels.return_value = [{"name": "bug"}, {"name": "enhancement"}]
    client_instance.get_issues.return_value = []
    client_instance.get_file_content.return_value = None
    mock_gh.return_value = client_instance

    triage_res = TriageResult(
        type="bug",
        priority="high",
        classification_reasoning="Crash report",
        labels=["bug"]
    )
    mock_generate.return_value = triage_res

    import builtins
    orig_open = builtins.open
    def safe_open(file, mode="r", *args, **kwargs):
        if "w" in mode and "dashboard" in str(file):
            from unittest.mock import mock_open
            return mock_open()()
        return orig_open(file, mode, *args, **kwargs)

    with patch("builtins.open", side_effect=safe_open):
        run_triage_pipeline("testowner", "testrepo", 12)

    # Verify metric was recorded
    assert ISSUES_TRIAGED_TOTAL.labels(repo="testowner/testrepo", type="bug", priority="high")._value.get() >= 1
