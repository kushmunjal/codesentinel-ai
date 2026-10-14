import json
import logging
from datetime import UTC, datetime
from typing import Any

_STANDARD_LOG_RECORD_ATTRS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
}


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter outputting timestamp, level, correlation IDs, and message."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "repo": getattr(record, "repo", None),
            "pr_number": getattr(record, "pr_number", None),
            "issue_number": getattr(record, "issue_number", None),
            "run_id": getattr(record, "run_id", None),
        }

        # Include custom extra fields passed on record
        for key, val in record.__dict__.items():
            if key not in _STANDARD_LOG_RECORD_ATTRS and key not in log_entry:
                try:
                    json.dumps(val)
                    log_entry[key] = val
                except (TypeError, OverflowError):
                    log_entry[key] = str(val)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_entry)


class CorrelationAdapter(logging.LoggerAdapter):
    """LoggerAdapter that attaches correlation IDs to all log records."""

    def __init__(
        self,
        logger: logging.Logger,
        repo: str | None = None,
        pr_number: int | None = None,
        issue_number: int | None = None,
        run_id: str | None = None,
        **extra: Any,
    ):
        defaults = {
            "repo": repo,
            "pr_number": pr_number,
            "issue_number": issue_number,
            "run_id": run_id,
        }
        defaults.update(extra)
        super().__init__(logger, defaults)

    def process(self, msg: Any, kwargs: Any):
        extra = dict(self.extra)
        if "extra" in kwargs:
            extra.update(kwargs["extra"])
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(
    name: str = "codesentinel",
    level: int = logging.INFO,
    repo: str | None = None,
    pr_number: int | None = None,
    issue_number: int | None = None,
    run_id: str | None = None,
) -> CorrelationAdapter:
    """Returns a logger equipped with JSONFormatter and optional correlation IDs."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Attach JSON handler if none exists for this logger
    if not any(isinstance(getattr(h, "formatter", None), JSONFormatter) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return CorrelationAdapter(
        logger,
        repo=repo,
        pr_number=pr_number,
        issue_number=issue_number,
        run_id=run_id,
    )
