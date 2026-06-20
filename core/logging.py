"""core.logging — structured JSON logging for kian_v2ray.

One-line JSON records (newline-delimited) so logs are greppable by humans and
parseable by Loki/Promtail/jq alike. No third-party dependency.

    from core.logging import get_logger
    log = get_logger("installer")
    log.info("user_added", name="ali", quota_gb=100)

Each record is: {"ts","time","level","logger","msg", **fields}. User-supplied
structured fields are carried in a single ``kian_fields`` LogRecord attribute so
they can never collide with reserved LogRecord names (e.g. ``name``, ``msg``).
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

_FIELDS_ATTR = "kian_fields"


class JsonFormatter(logging.Formatter):
    """Render a :class:`logging.LogRecord` as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": round(record.created, 3),
            "time": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        fields = getattr(record, _FIELDS_ATTR, None)
        if isinstance(fields, dict):
            for key, value in fields.items():
                if key not in payload:
                    payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class _StructuredLogger(logging.LoggerAdapter):
    """Lets callers pass structured fields as kwargs: log.info("msg", k=v)."""

    def process(self, msg, kwargs):
        passthrough = {"exc_info", "stack_info", "stacklevel"}
        fields = kwargs.pop("extra", {}) or {}
        for key in list(kwargs):
            if key not in passthrough:
                fields[key] = kwargs.pop(key)
        kwargs["extra"] = {_FIELDS_ATTR: fields}
        return msg, kwargs


def get_logger(name: str = "kian", level: int = logging.INFO,
               stream=None) -> _StructuredLogger:
    """Return a structured logger writing JSON lines to *stream* (stderr)."""
    logger = logging.getLogger(name)
    if not any(isinstance(h, logging.StreamHandler) and getattr(h, "_kian", False)
               for h in logger.handlers):
        handler = logging.StreamHandler(stream or sys.stderr)
        handler.setFormatter(JsonFormatter())
        handler._kian = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level)
    return _StructuredLogger(logger, {})
