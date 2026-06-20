"""Tests for the phase-4 scripts: kian-bot command handler + sub-format render.

Both filenames contain a hyphen, so they're loaded by path via importlib.
"""

from __future__ import annotations

import importlib.util
import json
import os

from core import migrate

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(relpath: str, name: str):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(_HERE, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_bot_handle_add_status_remove(tmp_path):
    bot = _load("scripts/kian-bot.py", "kian_bot")
    path = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(path)
    assert "added ali" in bot.handle("/add ali 100 30", path)
    assert "users: 1" in bot.handle("/status", path)
    assert "ali" in bot.handle("/users", path)
    assert "100" in bot.handle("/usage ali", path) or "GB" in bot.handle("/usage ali", path)
    assert "removed ali" in bot.handle("/remove ali", path)
    assert "no such user" in bot.handle("/usage ghost", path)
    assert "/status" in bot.handle("/help", path)


def test_sub_format_render():
    sf = _load("scripts/sub-format.py", "sub_format")
    proxies = [{"name": "x", "type": "vless", "server": "1.2.3.4",
                "port": 443, "uuid": "u", "tls": True}]
    singbox, ct = sf.render(proxies, "singbox")
    assert ct == "application/json"
    assert "outbounds" in json.loads(singbox)
    clash, ct2 = sf.render(proxies, "clash")
    assert "proxies:" in clash and ct2 == "text/yaml"
    b64, ct3 = sf.render(proxies, "base64")
    import base64 as _b
    assert "vless://" in _b.b64decode(b64).decode()
