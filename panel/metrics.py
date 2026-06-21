"""panel.metrics — Prometheus text exposition for the panel (stdlib only).

Kept dependency-free (no fastapi) so it is unit-testable and reusable.
"""

from __future__ import annotations


def render_metrics(stats: dict, node_count: int, alive_count: int) -> str:
    """Prometheus text exposition format (0.0.4) for the panel's own metrics."""
    lines = [
        "# HELP kian_users_total Total users.",
        "# TYPE kian_users_total gauge",
        f"kian_users_total {stats['total_users']}",
        "# HELP kian_users_active Active (enabled) users.",
        "# TYPE kian_users_active gauge",
        f"kian_users_active {stats['active_users']}",
        "# HELP kian_traffic_bytes_total Total traffic used across users.",
        "# TYPE kian_traffic_bytes_total counter",
        f"kian_traffic_bytes_total {stats['total_used_bytes']}",
        "# HELP kian_nodes_total Registered nodes.",
        "# TYPE kian_nodes_total gauge",
        f"kian_nodes_total {node_count}",
        "# HELP kian_nodes_alive Nodes seen recently.",
        "# TYPE kian_nodes_alive gauge",
        f"kian_nodes_alive {alive_count}",
    ]
    return "\n".join(lines) + "\n"
