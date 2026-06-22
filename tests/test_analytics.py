"""Tests for the opt-in anonymous analytics module — focus on privacy + safety.

Run: pytest -q
"""
from __future__ import annotations

import os

from core import analytics


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("KIAN_ANALYTICS", raising=False)
    assert analytics.enabled() is False
    # send() must be a no-op (False) when disabled, never raise
    assert analytics.send({"x": 1}, endpoint="http://example.invalid") is False


def test_enabled_only_with_flag(monkeypatch):
    monkeypatch.setenv("KIAN_ANALYTICS", "1")
    assert analytics.enabled() is True


def test_payload_has_no_pii():
    stats = {"total_users": 12, "active_users": 9, "total_used_bytes": 5 * 1024**3}
    p = analytics.build_payload(stats, install_id="rand123", version="panel",
                                protocols=["reality", "hysteria2"])
    blob = str(p).lower()
    # no IPs, no host, no user names, no raw byte counts
    assert "total_used_bytes" not in p
    assert p["traffic_bucket"] == "1-10GB"
    assert p["users_total"] == 12 and p["users_active"] == 9
    assert "ip" not in p and "host" not in p and "server" not in blob
    assert p["protocols"] == ["hysteria2", "reality"]  # sorted


def test_traffic_buckets():
    mk = lambda gb: analytics.build_payload(  # noqa: E731
        {"total_used_bytes": int(gb * 1024**3)}, install_id="x", version="v")
    assert mk(0.5)["traffic_bucket"] == "<1GB"
    assert mk(5)["traffic_bucket"] == "1-10GB"
    assert mk(50)["traffic_bucket"] == "10-100GB"
    assert mk(500)["traffic_bucket"] == "100GB-1TB"
    assert mk(2000)["traffic_bucket"] == ">1TB"


def test_send_fails_closed_on_bad_endpoint(monkeypatch):
    monkeypatch.setenv("KIAN_ANALYTICS", "1")
    # unreachable endpoint must not raise, returns False
    assert analytics.send({"a": 1}, endpoint="http://127.0.0.1:9/none",
                          timeout=0.5) is False
