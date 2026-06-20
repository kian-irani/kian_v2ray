"""Tests for the standalone scripts (config-health validation logic).

The script filename has a hyphen, so we load it by path via importlib.
"""

from __future__ import annotations

import importlib.util
import os

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(relpath: str, name: str):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(_HERE, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_config_health_accepts_valid_reality():
    ch = _load("scripts/config-health.py", "config_health")
    cfg = {
        "inbounds": [
            {
                "tag": "reality-1", "protocol": "vless", "port": 443,
                "streamSettings": {
                    "security": "reality",
                    "realitySettings": {
                        "privateKey": "k", "shortIds": ["ab"],
                        "serverNames": ["www.speedtest.net"],
                    },
                },
            },
            {
                "tag": "ss-1", "protocol": "shadowsocks", "port": 8388,
                "settings": {"method": "2022-blake3-aes-256-gcm"},
            },
        ]
    }
    assert ch.check_config(cfg) == []


def test_config_health_flags_problems():
    ch = _load("scripts/config-health.py", "config_health2")
    cfg = {
        "inbounds": [
            {"tag": "a", "protocol": "vless", "port": 443,
             "streamSettings": {"security": "reality",
                                "realitySettings": {}}},
            # duplicate port + weak cipher + unknown protocol
            {"tag": "b", "protocol": "shadowsocks", "port": 443,
             "settings": {"method": "rc4-md5"}},
            {"tag": "c", "protocol": "bogus", "port": 9},
        ]
    }
    problems = ch.check_config(cfg)
    joined = " ".join(problems)
    assert "missing privateKey" in joined
    assert "already used" in joined
    assert "weak/unknown cipher" in joined
    assert "unknown protocol" in joined


def test_config_health_empty_inbounds():
    ch = _load("scripts/config-health.py", "config_health3")
    assert ch.check_config({"inbounds": []}) == ["no inbounds defined"]
