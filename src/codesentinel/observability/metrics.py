from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Reviews
REVIEWS_TOTAL = Counter(
    "codesentinel_reviews_total",
    "Total PR reviews executed",
    ["repo", "risk", "status"]
)

# Findings
FINDINGS_TOTAL = Counter(
    "codesentinel_findings_total",
    "Total review findings by category and severity",
    ["repo", "severity", "category"]
)

# Triage
ISSUES_TRIAGED_TOTAL = Counter(
    "codesentinel_issues_triaged_total",
    "Total issues triaged",
    ["repo", "type", "priority"]
)

# LLM Operations
LLM_REQUESTS_TOTAL = Counter(
    "codesentinel_llm_requests_total",
    "Total LLM API requests",
    ["model", "status"]
)

LLM_LATENCY_SECONDS = Histogram(
    "codesentinel_llm_latency_seconds",
    "LLM API request latency in seconds",
    ["model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

LLM_TOKENS_TOTAL = Counter(
    "codesentinel_llm_tokens_total",
    "Total LLM tokens consumed",
    ["model", "direction"]  # prompt or completion
)

LLM_COST_DOLLARS_TOTAL = Counter(
    "codesentinel_llm_cost_dollars_total",
    "Estimated LLM cost in USD",
    ["model"]
)

# Cache
CACHE_HITS_TOTAL = Counter(
    "codesentinel_cache_hits_total",
    "Total cache hits",
    ["cache"]
)

CACHE_MISSES_TOTAL = Counter(
    "codesentinel_cache_misses_total",
    "Total cache misses",
    ["cache"]
)

# Active Gauges
ACTIVE_REVIEWS_GAUGE = Gauge(
    "codesentinel_active_reviews_count",
    "Currently running reviews"
)

# Maintainer Feedback
FEEDBACK_TOTAL = Counter(
    "codesentinel_feedback_total",
    "Maintainer feedback on findings",
    ["type"]  # useful, false_positive
)

def get_metrics_payload():
    return generate_latest(), CONTENT_TYPE_LATEST

def get_metrics_summary(db=None) -> dict:
    """Aggregates Prometheus metrics into a JSON summary for dashboards."""
    reviews_total = 0.0
    reviews_error = 0.0
    cache_hits = 0.0
    cache_misses = 0.0
    prompt_tokens = 0.0
    completion_tokens = 0.0
    latency_sum = 0.0
    latency_count = 0.0

    for metric in REGISTRY.collect():
        for s in metric.samples:
            if s.name == "codesentinel_reviews_total":
                reviews_total += s.value
                if s.labels.get("status") == "error":
                    reviews_error += s.value
            elif s.name == "codesentinel_cache_hits_total":
                cache_hits += s.value
            elif s.name == "codesentinel_cache_misses_total":
                cache_misses += s.value
            elif s.name == "codesentinel_llm_tokens_total":
                if s.labels.get("direction") == "prompt":
                    prompt_tokens += s.value
                elif s.labels.get("direction") == "completion":
                    completion_tokens += s.value
            elif s.name == "codesentinel_llm_latency_seconds_sum":
                latency_sum += s.value
            elif s.name == "codesentinel_llm_latency_seconds_count":
                latency_count += s.value

    if reviews_total == 0 and db is not None:
        try:
            from codesentinel.api.database import PRState
            reviews_total = float(db.query(PRState).count())
        except (AttributeError, RuntimeError):
            pass

    cache_total = cache_hits + cache_misses
    cache_hit_rate = (cache_hits / cache_total) if cache_total > 0 else 0.0
    error_rate = (reviews_error / reviews_total) if reviews_total > 0 else 0.0
    avg_latency = (latency_sum / latency_count) if latency_count > 0 else 0.0
    total_tokens = prompt_tokens + completion_tokens

    return {
        "reviews_count": int(reviews_total),
        "error_rate": round(error_rate, 4),
        "cache_hit_rate": round(cache_hit_rate, 4),
        "token_counts": {
            "prompt": int(prompt_tokens),
            "completion": int(completion_tokens),
            "total": int(total_tokens),
        },
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "total_tokens": int(total_tokens),
        "avg_latency": round(avg_latency, 4),
    }
