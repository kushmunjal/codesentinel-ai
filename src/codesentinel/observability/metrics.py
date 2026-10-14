from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

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
