"""core.cluster — multi-server orchestration logic (phase 5).

Pure decision functions over node descriptors so they're fully unit-testable
without real servers. A *node* dict looks like:

    {"name","address","geo","enabled","healthy","load","last_seen"}

Used by the panel to choose where to send a user (failover, load balance,
geo-routing) and to raise bandwidth alerts.
"""

from __future__ import annotations

import time
from typing import Iterable, Optional

HEALTHY_WINDOW = 90   # seconds since last_seen to still count as alive


def is_alive(node: dict, *, now: Optional[int] = None) -> bool:
    ts = int(now if now is not None else time.time())
    last = node.get("last_seen")
    return bool(node.get("enabled", 1)) and last is not None and (ts - last) <= HEALTHY_WINDOW


def healthy_nodes(nodes: Iterable[dict], *, now: Optional[int] = None) -> list[dict]:
    return [n for n in nodes if is_alive(n, now=now) and n.get("healthy", True)]


def pick_least_loaded(nodes: Iterable[dict], *,
                      now: Optional[int] = None) -> Optional[dict]:
    """Load balancing: the alive node with the lowest reported load."""
    alive = healthy_nodes(nodes, now=now)
    if not alive:
        return None
    return min(alive, key=lambda n: (n.get("load", 0.0), n["name"]))


def failover_order(nodes: Iterable[dict], *,
                   now: Optional[int] = None) -> list[str]:
    """Ordered node names to try: healthy first (least loaded), then the rest."""
    nodes = list(nodes)
    alive = sorted(healthy_nodes(nodes, now=now),
                   key=lambda n: (n.get("load", 0.0), n["name"]))
    # Compare by the unique "name" key, not by whole-dict value: two distinct
    # nodes with identical telemetry would otherwise be treated as equal and
    # one of them silently dropped from the failover list. (also O(n) vs O(n^2))
    alive_names = {n["name"] for n in alive}
    dead = [n for n in nodes if n["name"] not in alive_names]
    return [n["name"] for n in alive] + [n["name"] for n in dead]


# Coarse region map: country code -> region bucket, and node geo -> region.
_COUNTRY_REGION = {
    "IR": "me", "TR": "me", "AE": "me", "QA": "me",
    "DE": "eu", "NL": "eu", "FR": "eu", "GB": "eu", "FI": "eu",
    "US": "na", "CA": "na",
    "SG": "as", "JP": "as", "HK": "as",
}


def route_by_geo(country: str, nodes: Iterable[dict], *,
                 now: Optional[int] = None) -> Optional[dict]:
    """Pick the alive node geographically closest to *country*."""
    alive = healthy_nodes(nodes, now=now)
    if not alive:
        return None
    region = _COUNTRY_REGION.get((country or "").upper(), "eu")
    # prefer same region, then least loaded
    same = [n for n in alive
            if _COUNTRY_REGION.get((n.get("geo") or "").upper()) == region]
    pool = same or alive
    return min(pool, key=lambda n: (n.get("load", 0.0), n["name"]))


def bandwidth_alerts(nodes: Iterable[dict], *,
                     threshold_gb: float = 900.0) -> list[dict]:
    """Nodes whose monthly bandwidth crossed the alert threshold."""
    out = []
    for n in nodes:
        used = n.get("bandwidth_gb", 0.0)
        if used >= threshold_gb:
            out.append({"name": n["name"], "bandwidth_gb": used,
                        "threshold_gb": threshold_gb})
    return out
