"""Anonymous, opt-in usage analytics (roadmap phase 7).

Privacy-first by design:
* **Opt-in only** — does nothing unless ``KIAN_ANALYTICS=1`` is set.
* **No personal data** — no IPs, no user names, no configs, no server addresses.
  Only coarse counts and a random, rotating install id.
* **Transparent** — :func:`build_payload` returns exactly what would be sent so
  it can be logged/inspected before anything leaves the box.

The point is to let an operator *voluntarily* share aggregate health (how many
users, which protocols are enabled) to help prioritise development — never to
phone home silently. Sending is a thin stdlib POST with a short timeout that
fails closed (never raises into the caller).
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Optional

_ENV_FLAG = "KIAN_ANALYTICS"          # "1" to enable
_ENV_ENDPOINT = "KIAN_ANALYTICS_URL"  # where to POST (operator-chosen)


def enabled() -> bool:
    """True only when the operator explicitly opted in."""
    return os.environ.get(_ENV_FLAG, "0") == "1"


def build_payload(stats: dict[str, Any], *, install_id: str,
                  version: str, protocols: Optional[list[str]] = None) -> dict[str, Any]:
    """The exact (anonymous) document that would be sent. No PII — only counts.

    ``install_id`` should be a random, non-identifying token (e.g. the panel's
    rotating id), never something derived from the host/IP.
    """
    return {
        "schema": 1,
        "install_id": install_id,
        "version": version,
        "users_total": int(stats.get("total_users", 0)),
        "users_active": int(stats.get("active_users", 0)),
        # bytes are bucketed to an order of magnitude, not exact
        "traffic_bucket": _bucket(int(stats.get("total_used_bytes", 0))),
        "protocols": sorted(protocols or []),
    }


def _bucket(n: int) -> str:
    """Coarsen a byte count to a privacy-safe magnitude bucket."""
    gb = n / (1024 ** 3)
    for limit, label in ((1, "<1GB"), (10, "1-10GB"), (100, "10-100GB"),
                         (1024, "100GB-1TB")):
        if gb < limit:
            return label
    return ">1TB"


def send(payload: dict[str, Any], *, endpoint: Optional[str] = None,
         timeout: float = 5.0) -> bool:
    """POST the payload if enabled + an endpoint is configured. Fails closed
    (returns False, never raises) so analytics can't break the panel."""
    if not enabled():
        return False
    url = endpoint or os.environ.get(_ENV_ENDPOINT, "")
    if not url:
        return False
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return 200 <= resp.status < 300
    except Exception:
        return False
