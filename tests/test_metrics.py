"""Tests for panel.metrics Prometheus exposition (phase 7.4 wiring)."""

from __future__ import annotations

from panel.metrics import render_metrics


def test_render_metrics_format():
    out = render_metrics(
        {"total_users": 5, "active_users": 3, "total_used_bytes": 123},
        node_count=2, alive_count=1)
    assert "kian_users_total 5" in out
    assert "kian_users_active 3" in out
    assert "kian_traffic_bytes_total 123" in out
    assert "kian_nodes_total 2" in out
    assert "kian_nodes_alive 1" in out
    # every metric must be preceded by HELP + TYPE
    assert out.count("# TYPE") == 5
    assert out.endswith("\n")
