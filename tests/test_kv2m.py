"""Tests for kv2m multi-server store + updater version logic (phase 3)."""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_HERE, "kv2m"))

import servers as kv_servers  # noqa: E402
import updater as kv_updater  # noqa: E402


def test_server_store_add_select_remove(tmp_path):
    path = os.path.join(str(tmp_path), "servers.json")
    store = kv_servers.ServerStore(path)
    a = store.add(kv_servers.ServerProfile(name="de", host="1.1.1.1"))
    assert store.active == "de"           # first becomes active
    store.add(kv_servers.ServerProfile(name="nl", host="2.2.2.2", port=2222))
    assert len(store.profiles) == 2

    # persistence round-trip
    store2 = kv_servers.ServerStore(path)
    assert {p.name for p in store2.profiles} == {"de", "nl"}
    assert store2.get("nl").port == 2222

    store2.select("nl")
    assert store2.active == "nl"
    assert store2.active_profile().host == "2.2.2.2"

    assert store2.remove("de") is True
    assert store2.get("de") is None
    assert a.name == "de"


def test_server_store_rejects_duplicate(tmp_path):
    store = kv_servers.ServerStore(os.path.join(str(tmp_path), "s.json"))
    store.add(kv_servers.ServerProfile(name="x", host="1.1.1.1"))
    try:
        store.add(kv_servers.ServerProfile(name="x", host="9.9.9.9"))
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_updater_version_compare():
    assert kv_updater.parse_version("v3.0.2") == (3, 0, 2)
    assert kv_updater.parse_version("kv2m-3.1.0") == (3, 1, 0)
    assert kv_updater.is_newer("v3.1.0", "3.0.9")
    assert not kv_updater.is_newer("v3.0.0", "3.0.0")
    assert not kv_updater.is_newer("v2.9.9", "v3.0.0")
