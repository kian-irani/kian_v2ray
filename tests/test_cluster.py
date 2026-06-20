"""Tests for core.cluster + node repo + migration importer + node-agent (phase 5)."""

from __future__ import annotations

import importlib.util
import os
import sys

from core import cluster, db, migrate
from panel import repo

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(relpath: str, name: str):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(_HERE, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


NOW = 1_000_000


def _nodes():
    return [
        {"name": "de", "geo": "DE", "enabled": 1, "healthy": True,
         "load": 0.8, "last_seen": NOW - 10, "bandwidth_gb": 950},
        {"name": "nl", "geo": "NL", "enabled": 1, "healthy": True,
         "load": 0.2, "last_seen": NOW - 5, "bandwidth_gb": 100},
        {"name": "us", "geo": "US", "enabled": 1, "healthy": True,
         "load": 0.1, "last_seen": NOW - 9999, "bandwidth_gb": 10},  # stale
    ]


# ---------- cluster ----------

def test_health_and_least_loaded():
    ns = _nodes()
    alive = cluster.healthy_nodes(ns, now=NOW)
    assert {n["name"] for n in alive} == {"de", "nl"}     # us is stale
    assert cluster.pick_least_loaded(ns, now=NOW)["name"] == "nl"


def test_failover_order_alive_first():
    order = cluster.failover_order(_nodes(), now=NOW)
    assert order[0] == "nl" and order[1] == "de"
    assert order[-1] == "us"   # stale node last


def test_geo_routing_prefers_region():
    # IR maps to "me"; no me node alive -> falls back to least loaded alive
    assert cluster.route_by_geo("IR", _nodes(), now=NOW)["name"] == "nl"
    # a German user -> EU region -> nl/de both eu, least loaded = nl
    assert cluster.route_by_geo("DE", _nodes(), now=NOW)["name"] == "nl"


def test_bandwidth_alerts():
    alerts = cluster.bandwidth_alerts(_nodes(), threshold_gb=900)
    assert len(alerts) == 1 and alerts[0]["name"] == "de"


# ---------- node repo + migration 0005 ----------

def test_node_repo_and_heartbeat(tmp_path):
    path = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(path)
    with db.session(path) as conn:
        repo.upsert_node(conn, actor="root", name="de", address="1.2.3.4",
                         token="t", geo="DE")
        assert repo.node_heartbeat(conn, name="de", load=0.5,
                                   bandwidth_gb=42, now=NOW)
        nodes = repo.list_nodes(conn)
        assert nodes[0]["load"] == 0.5 and nodes[0]["bandwidth_gb"] == 42
        assert cluster.is_alive(nodes[0], now=NOW)
        assert repo.delete_node(conn, actor="root", name="de")


# ---------- migration importer ----------

def test_marzban_and_xui_normalize():
    mig = _load("scripts/migrate-import.py", "migrate_import")
    users = mig.normalize_marzban({"users": [
        {"username": "ali", "data_limit": 1000, "expire": 99, "status": "active"},
        {"username": "off", "status": "disabled"},
        {"data_limit": 5},  # no username -> skipped
    ]})
    assert len(users) == 2
    assert users[0]["name"] == "ali" and users[0]["quota_bytes"] == 1000
    assert users[1]["enabled"] == 0


def test_migration_import_into_db(tmp_path):
    mig = _load("scripts/migrate-import.py", "migrate_import2")
    path = os.path.join(str(tmp_path), "kian.db")
    users = [{"name": "ali", "quota_bytes": 100, "expires_at": None, "enabled": 1},
             {"name": "ali", "quota_bytes": 200, "expires_at": None, "enabled": 1}]
    res = mig.import_users(users, path)
    assert res["added"] == 1 and res["skipped"] == 1


# ---------- node agent ----------

def test_agent_apply_config(tmp_path):
    agent = _load("node-agent/agent.py", "node_agent")
    path = os.path.join(str(tmp_path), "config.json")
    ok, msg = agent.apply_config({"inbounds": [{"tag": "a", "port": 443}]}, path)
    assert ok and "1 inbound" in msg
    bad, _ = agent.apply_config({"no": "inbounds"}, path)
    assert not bad
