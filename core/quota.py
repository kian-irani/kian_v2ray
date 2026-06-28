"""core.quota — periodic traffic-quota reset scheduling (FR-S1).

Pure, calendar-aware helpers that decide *when* a user's used traffic should be
zeroed, given a reset strategy. No DB or I/O here so it stays fully
unit-testable; :func:`panel.repo.apply_quota_resets` applies the decision.

A *strategy* is one of:
    None / "" / "none"  -> never reset (the default; quota is a lifetime cap)
    "daily"             -> reset at 00:00 UTC each day
    "weekly"            -> reset at 00:00 UTC each Monday
    "monthly"           -> reset at 00:00 UTC on the 1st of each month
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Optional

VALID_STRATEGIES = ("daily", "weekly", "monthly")


def _utc(now: Optional[int]) -> datetime:
    ts = int(now if now is not None else time.time())
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def period_start(strategy: Optional[str], *, now: Optional[int] = None) -> Optional[int]:
    """Unix ts (UTC) of the start of the current period for *strategy*.

    Returns ``None`` when the strategy is empty/``none`` (no periodic reset).
    """
    s = (strategy or "").strip().lower()
    if s not in VALID_STRATEGIES:
        return None
    dt = _utc(now)
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if s == "daily":
        start = midnight
    elif s == "weekly":
        start = midnight - timedelta(days=dt.weekday())  # Monday=0
    else:  # monthly
        start = midnight.replace(day=1)
    return int(start.timestamp())


def is_due(strategy: Optional[str], last_reset: Optional[int], *,
           now: Optional[int] = None) -> bool:
    """True if a reset is due: the strategy is periodic and the last reset
    happened before the current period started (or never happened)."""
    start = period_start(strategy, now=now)
    if start is None:
        return False
    if last_reset is None:
        return True
    return int(last_reset) < start
