"""core.censorship — anti-censorship helpers (phase 4).

* REALITY SNI candidate ranking — score domains for how well they work as a
  REALITY front (TLS 1.3, popular CDN, not commonly blocked from Iran). This is
  the offline brain of the "REALITY IP scanner"; the live TLS probe runs on the
  server and feeds these scores.
* Tor bridge fallback — build an obfs4 / Snowflake outbound so traffic has a
  last-resort path when every direct protocol is blocked.
"""

from __future__ import annotations

from typing import Iterable

# Domains widely usable as REALITY fronts (TLS1.3, big CDNs, usually reachable).
_GOOD_FRONTS = {
    "www.speedtest.net", "www.cloudflare.com", "cdn.jsdelivr.net",
    "www.microsoft.com", "www.apple.com", "gateway.icloud.com",
    "www.nvidia.com", "www.samsung.com", "www.bing.com",
}
# Substrings that hurt a candidate (often blocked or no TLS1.3).
_BAD_HINTS = (".ir", "google", "youtube", "facebook", "twitter", "instagram")


def score_sni(domain: str) -> int:
    """Heuristic 0..100 — higher is a better REALITY front."""
    d = domain.lower().strip()
    if not d or "." not in d:
        return 0
    score = 50
    if d in _GOOD_FRONTS:
        score += 40
    if d.startswith("www."):
        score += 5
    if any(h in d for h in _BAD_HINTS):
        score -= 60
    if d.endswith((".com", ".net", ".org")):
        score += 5
    return max(0, min(100, score))


def rank_sni_candidates(candidates: Iterable[str]) -> list[dict]:
    """Return candidates sorted best-first with their scores."""
    ranked = [{"domain": c, "score": score_sni(c)} for c in candidates]
    ranked.sort(key=lambda x: (-x["score"], x["domain"]))
    return ranked


def best_sni(candidates: Iterable[str], minimum: int = 60) -> str | None:
    ranked = rank_sni_candidates(candidates)
    return ranked[0]["domain"] if ranked and ranked[0]["score"] >= minimum else None


def tor_bridge_outbound(mode: str = "obfs4",
                        bridge_line: str | None = None) -> dict:
    """Build a Tor fallback outbound descriptor (obfs4 or snowflake)."""
    if mode not in ("obfs4", "snowflake"):
        raise ValueError("mode must be obfs4 or snowflake")
    ob: dict = {"type": "tor", "tag": "tor-fallback", "mode": mode}
    if mode == "obfs4" and bridge_line:
        ob["bridges"] = [bridge_line]
    if mode == "snowflake":
        ob["broker"] = "https://snowflake-broker.torproject.net/"
    return ob


def fallback_routing_rule(primary_tag: str, fallback_tag: str = "tor-fallback") -> dict:
    """A routing rule: when the primary outbound is down, use the Tor fallback."""
    return {"type": "field", "balancerTag": None,
            "outboundTag": primary_tag, "fallbackTag": fallback_tag}
